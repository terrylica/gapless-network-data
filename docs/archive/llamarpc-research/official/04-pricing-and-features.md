# LlamaRPC Pricing and Features

**Date**: 2025-11-03
**Source**: https://llamanodes.com/pricing

## Pricing Tiers

### Trader Tier (FREE)

**Cost**: $0/month

**Features**:

- MEV Protection
- Private Transactions
- Low-Latency for Traders
- Community Support
- Public endpoints (https://eth.llamarpc.com, https://polygon.llamarpc.com, etc.)
- Custom API keys with usage dashboard

**Rate Limits** (from testing + website):

- 50 Requests per Second (documented)
- ~30-35 request burst limit (empirically observed)
- Sustained ~12 RPS (empirically observed)

**Signup**: "Get your Free RPC" - requires Web3 wallet connection

---

### Premium Tier (PAY-AS-YOU-GO)

**Cost**: Variable based on usage (compute units)

**Pricing Model**:

- Only pay for successful requests
- Example: 100,000 CU/month = $0.04/month
- 25% discount on repeated requests (intelligent caching)
- Interactive calculator on pricing page

**Features**:

- ✅ Unlimited Endpoints
- ✅ Unlimited Requests (no rate limiting)
- ✅ Infinite Scalability (auto-scaling)
- ✅ Archival Data on Demand
- ✅ Tracing Methods on Demand
- ✅ Advanced Monitoring Dashboard
- ✅ Global Coverage
- ✅ Low-Latency for dApps
- ✅ 24/7 Direct Support
- ✅ MEV Protection
- ✅ Error Mitigation (no charge for failed requests)

**Payment Methods**:

- Major stablecoins (crypto payments)
- Credit cards
- No contracts, pay-as-you-go

**Key Advantages**:

1. **Intelligent Routing**: Archival requests only routed to archive nodes when necessary (cost savings)
2. **Error Mitigation**: Failed requests don't count toward billing
3. **Caching**: 25% discount on repeated requests automatically applied
4. **No Rate Limits**: Truly unlimited RPS

---

### Enterprise Tier (CUSTOM)

**Threshold**: >1 billion requests/month

**Features**:

- Custom Service Level Agreements (SLAs)
- 24/7 engineering support
- Discounted pricing (volume-based)
- Dedicated account management

**Contact**: Requires direct sales contact

---

## Feature Comparison Matrix

| Feature                     | Free (Trader) | Premium | Enterprise |
| --------------------------- | ------------- | ------- | ---------- |
| MEV Protection              | ✅            | ✅      | ✅         |
| Private Transactions        | ✅            | ✅      | ✅         |
| Low Latency                 | ✅            | ✅      | ✅         |
| Rate Limiting               | 50 RPS        | ♾️ None | ♾️ None    |
| Archival Data               | ✅ (Free!)    | ✅      | ✅         |
| Tracing Methods             | ❌            | ✅      | ✅         |
| Advanced Dashboard          | Basic         | ✅      | ✅         |
| Support                     | Community     | 24/7    | 24/7 + Eng |
| Custom Endpoints            | Limited       | ♾️      | ♾️         |
| SLA Guarantees              | ❌            | ❌      | ✅         |
| Intelligent Caching Savings | ❌            | 25%     | 25%+       |
| Error Mitigation            | ❌            | ✅      | ✅         |

---

## Compute Units (CU) Explained

**Definition**: Pricing based on compute units consumed per request

**Cost Structure**:

- Example: 100,000 CU = $0.04
- Implies: 1 CU ≈ $0.0000004 ($0.40 per million CU)
- Scale estimate: 2.5 million CU per $1

**CU Consumption Varies By**:

- Method complexity (eth_call vs eth_blockNumber)
- Archival vs recent data
- Response size

**Cost-Saving Mechanisms**:

1. Caching (25% off repeated requests)
2. Smart routing (archive only when needed)
3. Error mitigation (failed = free)

---

## Free Tier Limitations (Empirically Verified)

From our testing (see 03-empirical-testing.md):

**Documented**:

- 50 RPS limit

**Observed Reality**:

- Burst limit: ~30-35 requests before HTTP 429
- Sustained rate: ~12 RPS in rapid testing
- HTTP 429 errors enforced for rate violations

**Archive Access**: FREE TIER HAS FULL ARCHIVE ACCESS (tested back to Block 1)

**Conclusion**: Free tier extremely generous for development, testing, and low-volume production. For >30 RPS sustained, upgrade to Premium.

---

## Premium Tier Value Analysis

**Cost Efficiency**:

- 100K requests/month = $0.04/month
- 1M requests/month ≈ $0.40/month
- 10M requests/month ≈ $4/month
- 100M requests/month ≈ $40/month

**Comparison to Competitors**:

- Alchemy: $199/month for 3M CU (Infinity tier)
- Infura: $50/month for 100K requests (Plus tier)
- QuickNode: $9/month for 5M credits (Discover tier)
- **LlamaNodes**: $0.04 for 100K requests (Premium tier)

**LlamaNodes Advantage**: 10-100x cheaper than major competitors for similar usage

---

## Payment Methods

**Crypto (Web3-native)**:

- Major stablecoins supported (USDC, USDT likely)
- Web3 wallet authentication
- Privacy-preserving (no KYC required)

**Traditional**:

- Credit card payments accepted
- Standard billing cycles

**Philosophy**: "No contracts" - pure pay-as-you-go, cancel anytime

---

## Signup Process (Inferred)

**Free Tier**:

1. Visit llamarpc.com or llamanodes.com
2. Connect Web3 wallet (MetaMask, etc.)
3. Sign authentication message
4. Receive custom API key
5. Access usage dashboard

**Premium Tier**:

1. Start with Free tier
2. Add payment method (crypto or card)
3. Automatically upgrade on usage
4. Pay-as-you-go billing

**Enterprise**:

1. Contact sales team
2. Negotiate custom SLA and pricing
3. Dedicated onboarding

---

## Key Differentiators

**vs Alchemy/Infura**:

- 10-100x lower cost
- No tiered plan restrictions
- True unlimited scaling
- Crypto payments (privacy)

**vs Self-Hosted Nodes**:

- No infrastructure maintenance
- Global CDN/low latency
- Auto-scaling
- MEV protection built-in

**vs Other Public RPCs**:

- Free tier has archive access
- Privacy-first (no tracking)
- Advanced monitoring dashboard
- 24/7 support on premium

---

## Documentation Quality Assessment

**Strengths**:

- Clear pricing calculator
- Transparent feature comparison
- No hidden fees
- Pay-only-for-success model

**Weaknesses**:

- No detailed CU consumption table
- Method costs not itemized
- Archive query costs unclear
- Tracing method pricing unknown

**Recommendation**: For precise cost estimation, use interactive calculator or contact support with usage patterns.
