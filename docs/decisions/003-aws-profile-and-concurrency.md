# AWS deployment identity and small-account concurrency

The project uses the named `kabadi-setu` Identity Center profile. The developer chose the AdministratorAccess permission set for deployment. Application code runs under its separate Lambda role, restricted to the project table and link-secret parameter; it does not inherit the developer's permissions. Root access is rejected by deployment helpers.

The initial plan reserved two concurrent Lambda executions. Live preflight found the Mumbai account limit is only ten. AWS requires an unreserved pool when setting a positive function reservation, so that configuration would fail. We omit the reservation and keep the existing account limit rather than requesting an increase. HTTP route throttling stays at two requests/second with burst five. This is not a hard monthly spending cap.

An account-wide monthly budget, separate from the application stack, sends pre-credit alerts above $1, $5 and $10. It deliberately remains useful even before cost allocation tags activate. An existing $20 account budget is left untouched.

Reference: https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html
