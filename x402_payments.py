"""
x402 V2 Payment Protocol Integration
Enables stablecoin-based micropayments for AI agent transactions.

Based on Coinbase's x402 V2 specification:
- Wallet-based identity (skip repaying on every call)
- Automatic API discovery
- Dynamic payment recipients
- Multi-chain/fiat support via CAIP standards
"""

from __future__ import annotations

import os
import json
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import httpx
from pydantic import BaseModel, Field


class PaymentNetwork(str, Enum):
    """Supported blockchain networks for x402 payments"""
    BASE = "eip155:8453"  # Base (L2)
    ETHEREUM = "eip155:1"  # Ethereum mainnet
    SOLANA = "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp"
    POLYGON = "eip155:137"


class PaymentScheme(str, Enum):
    """Payment schemes supported by x402"""
    EXACT = "exact"  # Pay per request
    SESSION = "session"  # Wallet-controlled sessions
    SUBSCRIPTION = "subscription"  # Recurring payments
    PREPAID = "prepaid"  # Credit-based


@dataclass
class PaymentRequirement:
    """x402 PaymentRequired response structure"""
    network: PaymentNetwork
    asset: str = "USDC"
    amount: str = "0"  # In smallest unit (e.g., 6 decimals for USDC)
    pay_to: str = ""  # Recipient address
    scheme: PaymentScheme = PaymentScheme.EXACT
    description: str = ""
    expires_at: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PaymentPayload:
    """x402 Payment signature payload"""
    network: str
    asset: str
    amount: str
    pay_to: str
    nonce: str
    signature: str
    wallet_address: str


class X402Client:
    """
    x402 V2 Client for AI agent payments.
    
    Enables agents to autonomously pay for services using stablecoins.
    """
    
    def __init__(
        self,
        wallet_address: Optional[str] = None,
        private_key: Optional[str] = None,
        facilitator_url: Optional[str] = None,
        default_network: PaymentNetwork = PaymentNetwork.BASE,
    ):
        self.wallet_address = wallet_address or os.getenv("X402_WALLET_ADDRESS")
        self.private_key = private_key or os.getenv("X402_PRIVATE_KEY")
        self.facilitator_url = facilitator_url or os.getenv(
            "X402_FACILITATOR_URL", 
            "https://x402.org/facilitator"
        )
        self.default_network = default_network
        self._session_token: Optional[str] = None
        self._session_expires: int = 0
    
    async def make_payment_request(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict] = None,
        max_amount_usd: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with x402 payment handling.
        
        If the server responds with 402 Payment Required, automatically
        handle the payment and retry the request.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            # First attempt
            response = await client.request(method, url, json=data)
            
            if response.status_code != 402:
                return response.json() if response.content else {}
            
            # Handle 402 Payment Required
            payment_required = self._parse_payment_required(response)
            
            # Validate payment amount
            amount_usd = float(payment_required.amount) / 1_000_000  # USDC has 6 decimals
            if amount_usd > max_amount_usd:
                raise ValueError(
                    f"Payment amount ${amount_usd:.4f} exceeds max ${max_amount_usd:.4f}"
                )
            
            # Create and sign payment
            payment = await self._create_payment(payment_required)
            
            # Retry with payment signature
            headers = {
                "PAYMENT-SIGNATURE": self._encode_payment(payment)
            }
            
            response = await client.request(method, url, json=data, headers=headers)
            response.raise_for_status()
            
            return response.json() if response.content else {}
    
    def _parse_payment_required(self, response: httpx.Response) -> PaymentRequirement:
        """Parse x402 PAYMENT-REQUIRED header"""
        header = response.headers.get("PAYMENT-REQUIRED", "")
        if not header:
            raise ValueError("Missing PAYMENT-REQUIRED header")
        
        # Decode base64 payment requirement
        import base64
        data = json.loads(base64.b64decode(header))
        
        return PaymentRequirement(
            network=PaymentNetwork(data.get("network", "eip155:8453")),
            asset=data.get("asset", "USDC"),
            amount=data.get("amount", "0"),
            pay_to=data.get("payTo", ""),
            scheme=PaymentScheme(data.get("scheme", "exact")),
            description=data.get("description", ""),
            expires_at=data.get("expiresAt"),
            metadata=data.get("metadata", {}),
        )
    
    async def _create_payment(self, requirement: PaymentRequirement) -> PaymentPayload:
        """Create a signed payment payload"""
        nonce = hashlib.sha256(f"{time.time()}:{self.wallet_address}".encode()).hexdigest()[:16]
        
        # In production, this would use web3.py or ethers to sign
        # For demo purposes, we create a placeholder signature
        message = f"{requirement.network}:{requirement.asset}:{requirement.amount}:{requirement.pay_to}:{nonce}"
        signature = self._sign_message(message)
        
        return PaymentPayload(
            network=requirement.network.value,
            asset=requirement.asset,
            amount=requirement.amount,
            pay_to=requirement.pay_to,
            nonce=nonce,
            signature=signature,
            wallet_address=self.wallet_address or "",
        )
    
    def _sign_message(self, message: str) -> str:
        """Sign a message with the wallet private key"""
        # Placeholder - in production use web3.py eth_account
        return hashlib.sha256(f"{self.private_key}:{message}".encode()).hexdigest()
    
    def _encode_payment(self, payment: PaymentPayload) -> str:
        """Encode payment payload for PAYMENT-SIGNATURE header"""
        import base64
        data = {
            "network": payment.network,
            "asset": payment.asset,
            "amount": payment.amount,
            "payTo": payment.pay_to,
            "nonce": payment.nonce,
            "signature": payment.signature,
            "walletAddress": payment.wallet_address,
        }
        return base64.b64encode(json.dumps(data).encode()).decode()
    
    async def get_session_token(self) -> str:
        """
        Get or create a reusable session token.
        
        x402 V2 supports wallet-controlled sessions to avoid
        paying on every call.
        """
        if self._session_token and time.time() < self._session_expires:
            return self._session_token
        
        # Create new session via facilitator
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.facilitator_url}/v1/sessions",
                json={
                    "walletAddress": self.wallet_address,
                    "network": self.default_network.value,
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._session_token = data.get("sessionToken")
                self._session_expires = data.get("expiresAt", time.time() + 3600)
        
        return self._session_token or ""


class X402Middleware:
    """
    FastAPI/Express middleware for accepting x402 payments.
    
    Enables your API to monetize endpoints with per-request
    stablecoin payments.
    """
    
    def __init__(
        self,
        facilitator_url: Optional[str] = None,
        pay_to: Optional[str] = None,
        default_network: PaymentNetwork = PaymentNetwork.BASE,
    ):
        self.facilitator_url = facilitator_url or os.getenv(
            "X402_FACILITATOR_URL",
            "https://x402.org/facilitator"
        )
        self.pay_to = pay_to or os.getenv("X402_PAY_TO_ADDRESS")
        self.default_network = default_network
        self.pricing: Dict[str, Dict] = {}
    
    def set_pricing(
        self,
        endpoint: str,
        amount_usd: float,
        description: str = "",
        scheme: PaymentScheme = PaymentScheme.EXACT,
    ):
        """Set pricing for an endpoint"""
        self.pricing[endpoint] = {
            "amount": str(int(amount_usd * 1_000_000)),  # Convert to USDC smallest unit
            "description": description,
            "scheme": scheme,
        }
    
    def create_payment_required_response(
        self,
        endpoint: str,
        dynamic_pay_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a 402 Payment Required response"""
        pricing = self.pricing.get(endpoint, {"amount": "10000", "description": endpoint})
        
        import base64
        requirement = {
            "network": self.default_network.value,
            "asset": "USDC",
            "amount": pricing["amount"],
            "payTo": dynamic_pay_to or self.pay_to,
            "scheme": pricing.get("scheme", "exact"),
            "description": pricing.get("description", ""),
            "expiresAt": int(time.time()) + 300,  # 5 minutes
        }
        
        return {
            "status_code": 402,
            "headers": {
                "PAYMENT-REQUIRED": base64.b64encode(
                    json.dumps(requirement).encode()
                ).decode()
            }
        }
    
    async def verify_payment(
        self,
        payment_signature: str,
        endpoint: str,
    ) -> bool:
        """Verify a payment signature via the facilitator"""
        import base64
        
        try:
            payment_data = json.loads(base64.b64decode(payment_signature))
            pricing = self.pricing.get(endpoint, {})
            
            # Verify via facilitator
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.facilitator_url}/v1/verify",
                    json={
                        "payment": payment_data,
                        "expectedAmount": pricing.get("amount", "0"),
                        "expectedPayTo": self.pay_to,
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("valid", False)
                    
        except Exception as e:
            print(f"Payment verification error: {e}")
        
        return False


class AgentPaymentManager:
    """
    Manages payments for AI agent operations.
    
    Tracks costs, enforces budgets, and handles inter-agent payments.
    """
    
    def __init__(
        self,
        budget_per_lead: float = 0.25,
        wallet_address: Optional[str] = None,
    ):
        self.budget_per_lead = budget_per_lead
        self.client = X402Client(wallet_address=wallet_address)
        self.cost_tracker: Dict[str, float] = {}
        self.transaction_log: List[Dict] = []
    
    async def pay_for_service(
        self,
        service_url: str,
        agent_name: str,
        lead_id: str,
        max_amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Pay for an external service on behalf of an agent.
        
        Automatically handles x402 payment flow.
        """
        max_cost = max_amount or (self.budget_per_lead - self.cost_tracker.get(lead_id, 0))
        
        if max_cost <= 0:
            raise ValueError(f"Budget exhausted for lead {lead_id}")
        
        result = await self.client.make_payment_request(
            url=service_url,
            max_amount_usd=max_cost,
        )
        
        # Track cost
        cost = result.get("_payment_amount", 0)
        self.cost_tracker[lead_id] = self.cost_tracker.get(lead_id, 0) + cost
        
        self.transaction_log.append({
            "timestamp": time.time(),
            "agent": agent_name,
            "lead_id": lead_id,
            "service": service_url,
            "amount": cost,
        })
        
        return result
    
    def get_remaining_budget(self, lead_id: str) -> float:
        """Get remaining budget for a lead"""
        return self.budget_per_lead - self.cost_tracker.get(lead_id, 0)
    
    def get_agent_costs(self) -> Dict[str, float]:
        """Get total costs by agent"""
        costs: Dict[str, float] = {}
        for tx in self.transaction_log:
            agent = tx["agent"]
            costs[agent] = costs.get(agent, 0) + tx["amount"]
        return costs


# FastAPI integration
def create_x402_fastapi_middleware(app, middleware: X402Middleware):
    """Add x402 payment middleware to FastAPI app"""
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    @app.middleware("http")
    async def x402_middleware(request: Request, call_next):
        endpoint = f"{request.method} {request.url.path}"
        
        # Check if endpoint requires payment
        if endpoint in middleware.pricing:
            payment_sig = request.headers.get("PAYMENT-SIGNATURE")
            
            if not payment_sig:
                # Return 402 Payment Required
                resp = middleware.create_payment_required_response(endpoint)
                return JSONResponse(
                    status_code=402,
                    content={"error": "Payment Required"},
                    headers=resp["headers"],
                )
            
            # Verify payment
            if not await middleware.verify_payment(payment_sig, endpoint):
                return JSONResponse(
                    status_code=402,
                    content={"error": "Invalid payment"},
                )
        
        return await call_next(request)


__all__ = [
    "X402Client",
    "X402Middleware",
    "AgentPaymentManager",
    "PaymentNetwork",
    "PaymentScheme",
    "PaymentRequirement",
    "PaymentPayload",
    "create_x402_fastapi_middleware",
]
