# Frontier RM Teams app

This directory contains the independently authored Teams manifest and Adaptive Card contracts for the Frontier RM Knowledge Assistant.

The Agents Toolkit scaffold is currently blocked because this workstation cannot establish TLS with the npm registry. Do not disable npm TLS verification. Once approved network access is available:

1. Run the required ATK CLI version check.
2. Scaffold a current code-based `teams-agent` project into a temporary directory.
3. Integrate the owned manifest copy and card builder without replacing the shared backend contract.
4. Test in Agents Playground, then in the target Teams tenant.
5. Confirm the Azure subscription and create `rg-frontier-rm-ebc-dev` before provisioning the bot registration or hosting resources.

The manifest placeholders must be resolved during packaging. The checked-in package is intentionally not sideload-ready and cannot create tenant resources.

## Run the local adapter

Start the shared API first, then the loopback-only Teams adapter:

```powershell
python services/api/server.py
python apps/teams/src/bot_server.py
```

The bot endpoint is `http://127.0.0.1:3978/api/messages` and its health endpoint is `http://127.0.0.1:3978/health`. It accepts only loopback Playground callback URLs and does not implement production Bot Connector authentication.

When Agents Playground is available:

```powershell
cd $HOME\Documents\Frontier-RM-Cockpit
agentsplayground -e http://127.0.0.1:3978/api/messages -c msteams
```

This uses Playground's built-in synthetic Teams context. Playground `0.2.27` validates a different custom-context schema than older examples, so this project deliberately does not ship an optional `.m365agentsplayground.yml` override.

Validate and create a placeholder-resolved local package with:

```powershell
python apps/teams/scripts/package_app.py --env playground --check
python apps/teams/scripts/package_app.py --env playground
```

The Playground package uses synthetic UUIDs and is not a tenant sideload package. A real package must be built only after tenant registration values are available.
<!-- end -->

