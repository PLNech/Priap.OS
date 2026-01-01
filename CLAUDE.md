# Priap.OS - LeekWars AI Agent

## Project Overview
Automated LeekWars agent with goal of RL-based combat AI. Browser automation + API integration.

## Development Philosophy: Empirical Agentic TDD

### Core Principles
1. **Test First, Discover Second** - Write small probing tests before building abstractions
2. **Iterative Discovery** - Use Playwright introspection to discover DOM/API structure empirically
3. **Fail Fast, Learn Fast** - Run experiments immediately, capture failures as documentation
4. **Living Documentation** - Update docs/ as discoveries are made, not after
5. **Build Tools as You Go** - Every repeated task is a tooling opportunity

### Tooling Philosophy
- **Identify repetition** - If you do something twice, consider automating it
- **Meta-tooling** - Tools that build tools accelerate exponentially
- **Layered automation**:
  - L0: Manual exploration (curl, browser)
  - L1: Scripts for specific tasks (login, fight, upload)
  - L2: Library abstractions (api.py, browser.py)
  - L3: Orchestration (batch runners, pipelines)
  - L4: Self-improving systems (RL, auto-tuning)
- **Invest in tooling early** - Time spent on good tools pays compound interest
- **Composable primitives** - Small, focused tools that combine well

### When Adding New Features
1. First: curl/browser test the endpoint/interaction manually
2. Second: Write a minimal probe script that captures the response
3. Third: Document findings in relevant docs/*.md
4. Fourth: Implement proper client method with error handling
5. Fifth: Add to test suite
6. **Sixth: Git commit after each successful milestone**

### Git Discipline
- **Commit after each success** - Small, atomic commits after each working feature
- **Descriptive messages** - What changed and why, not just "update"
- **Clean history** - Each commit should be a logical unit of work
- **Feature branches** - New features on branches, merge when stable

## Project Structure
```
src/leekwars_agent/    # Core library
  api.py               # HTTP API client
  browser.py           # Playwright automation
scripts/               # Probe/test scripts (run with poetry run python)
docs/                  # Living documentation
  API.md               # API endpoints discovered
  LEEK.md              # Game mechanics & strategy
screenshots/           # Browser debug captures
```

## Credentials
- Login: `leek@nech.pl`
- Account: PriapOS
- Leek: IAdonis (ID: 131321)

## Key API Notes
- Base URL: `https://leekwars.com/api/`
- Auth: JWT token via cookie after login
- Login requires: `login`, `password`, `keep_connected` params
- Token in `set-cookie: token=<jwt>` header

## Commands
```bash
# Run any script
poetry run python scripts/<script>.py

# Browser test (headful)
poetry run python scripts/login_test.py --browser

# API-only test
poetry run python scripts/login_test.py
```

## Long-term Goals
1. Full API coverage for game automation
2. Local fight simulation via leek-wars-generator (Java)
3. RL training for combat decisions (action selection, positioning)
4. Deploy trained policies as LeekScript AI

## Local Validation (Java)

**Always prefer local validation over online API** - it's faster, reliable, and works offline.

```bash
# Validate LeekScript locally
cd tools/leek-wars-generator
java -jar generator.jar --analyze <file.leek>
```

Requires Java 21+ (use SDKMAN: `sdk install java 21.0.5-tem`)

### LeekScript Gotchas
- `var` = block-scoped, `global` = file-scoped
- Use `global` for variables reassigned across blocks
- Error 33 = undefined reference, Error 35 = unused variable

## Data Capture for RL

Fight data structure for training:
```
data/
  actions: [...]     # Turn-by-turn action encoding
  leeks: [...]       # Entity states (pos, hp, tp, mp)
  map: {...}         # Grid, obstacles
```

Action codes: see docs/API.md "Action Encoding" section

## Resources
- [LeekWars API](https://leekwars.com/help/api)
- [Fight Generator](https://github.com/leek-wars/leek-wars-generator)
- [LeekScript](https://github.com/leek-wars/leekscript)
- [Java Utilities](https://github.com/LeBezout/LEEK-WARS)
