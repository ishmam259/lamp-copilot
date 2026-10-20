# Intent eval

**20 of 20 questions reached the right engine** (team-written 20/20, outside 0/0). Real model, recorded answers (`python eval/intent_eval.py`; `--record` calls OpenAI once). Correct = the answer called an acceptable tool; action requests also proposed the right action and left it waiting for the owner; out-of-scope questions touched no data.

| # | Question | Source | Expected | Result | Tools called |
|---|---|---|---|---|---|
| 1 | How much cash will I have next week? | team | get_forecast | right | tools ['get_forecast'] |
| 2 | When do I run short of money? | team | get_alerts, get_forecast, get_funding_plan | right | tools ['get_forecast'] |
| 3 | Which medicines are about to expire? | team | get_expiry | right | tools ['get_expiry', 'propose_action'] |
| 4 | How much do patients owe me in total? | team | get_accounts, get_dues | right | tools ['get_accounts'] |
| 5 | What were my sales in the last 30 days? | team | get_accounts | right | tools ['get_accounts'] |
| 6 | Did I make a profit this month? | team | get_accounts | right | tools ['get_accounts'] |
| 7 | Can I send the expiring Omeprazole back to the supplier? | team | get_expiry | right | tools ['get_expiry', 'propose_action'] |
| 8 | Should I order less from Supplier A? | team | get_orders, get_trim | right | tools ['get_orders', 'get_trim', 'propose_action'] |
| 9 | What orders do I have coming up? | team | get_orders | right | tools ['get_orders'] |
| 10 | How do I cover the shortfall on 26 October? | team | get_funding_plan | right | tools ['get_funding_plan', 'propose_action'] |
| 11 | What's the cheapest way to fill the cash gap? | team | get_funding_plan | right | tools ['get_funding_plan', 'propose_action'] |
| 12 | How much interest would the wallet loan cost me? | team | get_funding_plan | right | tools ['get_funding_plan', 'propose_action'] |
| 13 | What will a lender see about my shop? | team | get_passport | right | tools ['get_passport'] |
| 14 | Do I look reliable to a lender? How often do I pay suppliers on time? | team | get_passport | right | tools ['get_passport'] |
| 15 | Is there anything I should look at today? | team | get_alerts | right | tools ['get_alerts', 'propose_action'] |
| 16 | Ask Supplier A for 20 more days to pay. | team | propose_action → extension_request | right | tools ['get_dues', 'propose_action']; proposed ['extension_request'] |
| 17 | Please put money aside for the rent. | team | propose_action → set_aside | right | tools ['get_forecast', 'propose_action']; proposed ['set_aside'] |
| 18 | File a return claim for the expiring stock. | team | propose_action → return_claim | right | tools ['get_expiry', 'propose_action']; proposed ['return_claim'] |
| 19 | What's the weather in Dhaka tomorrow? | team | decline, no data tools | right | tools none |
| 20 | Write me a short poem about my pharmacy. | team | decline, no data tools | right | tools none |
