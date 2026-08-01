# MCP (Model Context Protocol) Setup Guide

## What is MCP?

MCP allows Claude Code to directly interact with external services like GitHub and Supabase without manual commands. Once configured, I can:

- ✅ Deploy Supabase Edge Functions automatically
- ✅ View and update GitHub Actions workflows  
- ✅ Read Supabase database directly
- ✅ Manage GitHub secrets and settings
- ✅ Check function logs in real-time

## Available MCP Servers

### 1. GitHub MCP Server
**Repository**: `github:modelcontextprotocol/servers/tree/main/src/github`

**Features**:
- Create/update/delete files
- Manage issues and pull requests
- View workflow runs
- Manage secrets
- Search code and repositories

### 2. Supabase MCP Server
**Repository**: Custom server (if available) or direct API integration

**Features**:
- Deploy Edge Functions
- Query database
- View function logs
- Manage environment variables
- Monitor database health

## Setup Instructions

### Step 1: Install MCP Servers

```bash
# Install GitHub MCP server
npm install -g @modelcontextprotocol/server-github

# Install Supabase MCP server (if available)
npm install -g @modelcontextprotocol/server-supabase
# OR use npx for one-time usage
```

### Step 2: Configure Claude Code

Edit your Claude Code settings to add MCP servers:

**File**: `~/.config/claude/config.json` (or similar path for macOS)

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "args": [],
      "env": {
        "GITHUB_TOKEN": "your-github-personal-access-token",
        "GITHUB_OWNER": "AsifArefinBonny",
        "GITHUB_REPO": "DailyCommit"
      }
    },
    "supabase": {
      "command": "mcp-server-supabase",
      "args": [],
      "env": {
        "SUPABASE_URL": "https://ybblpzymovvngtllrsbn.supabase.co",
        "SUPABASE_ACCESS_TOKEN": "your-supabase-access-token",
        "SUPABASE_PROJECT_REF": "ybblpzymovvngtllrsbn"
      }
    }
  }
}
```

### Step 3: Create GitHub Personal Access Token

1. Go to: https://github.com/settings/tokens/new
2. Select scopes:
   - ✅ `repo` (full repository access)
   - ✅ `workflow` (manage workflows)
   - ✅ `write:packages` (if needed)
3. Generate token and copy it
4. Add to Claude Code config as `GITHUB_TOKEN`

### Step 4: Get Supabase Access Token

1. Go to: https://supabase.com/dashboard/account/tokens
2. Click "Generate new token"
3. Name it: "Claude Code MCP"
4. Copy the token
5. Add to Claude Code config as `SUPABASE_ACCESS_TOKEN`

### Step 5: Restart Claude Code

```bash
# Close and reopen Claude Code terminal
# Or restart the Claude Code process
```

### Step 6: Verify Setup

Once MCP is configured, I'll have access to tools like:

```
mcp__github__create_or_update_file
mcp__github__push_files
mcp__github__get_file_contents
mcp__github__search_code
mcp__supabase__deploy_function
mcp__supabase__query_database
mcp__supabase__get_logs
```

## Alternative: Direct API Integration (Simpler)

If MCP servers aren't available, we can use direct API integration:

### For Supabase Deployments

Create a simple Python/Node.js script that uses Supabase Management API:

```bash
# Save Supabase access token as environment variable
echo 'export SUPABASE_ACCESS_TOKEN="your-token-here"' >> ~/.zshrc
source ~/.zshrc

# Now I can use it in bash commands
curl -X POST "https://api.supabase.com/v1/projects/ybblpzymovvngtllrsbn/functions/telegram-webhook/deploy" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @supabase/functions/telegram-webhook/index.ts
```

### For GitHub Operations

GitHub CLI (`gh`) already provides most automation:

```bash
# Already available and authenticated
gh workflow run daily.yml
gh secret set EMAIL_PASSWORD
gh api repos/AsifArefinBonny/DailyCommit/actions/runs
```

## Quick Setup (Recommended for Now)

**Option 1**: Set environment variables (simplest):

```bash
# Add to ~/.zshrc or ~/.bashrc
export SUPABASE_ACCESS_TOKEN="sbp_xxx..."
export GITHUB_TOKEN="ghp_xxx..."

source ~/.zshrc
```

Then I can use these directly in bash commands without manual input.

**Option 2**: Use GitHub CLI for GitHub + Environment variable for Supabase:

```bash
# GitHub: Already working via `gh` CLI
gh auth status  # ✅ Already authenticated

# Supabase: Set access token
export SUPABASE_ACCESS_TOKEN="your-token"

# Now deployment script will work:
./deploy_webhook.sh  # ✅ Will deploy automatically
```

## What Changes After MCP Setup?

### Before MCP:
```
You: Deploy the webhook
Me: Here's a script. Please run: ./deploy_webhook.sh
You: [runs script manually]
```

### After MCP:
```
You: Deploy the webhook
Me: [directly deploys via MCP] ✅ Deployed successfully
```

## Testing MCP Connection

After setup, ask me to:

1. "List all GitHub workflow runs"
2. "Deploy telegram-webhook to Supabase"
3. "Show latest Supabase function logs"

If I can do these without asking for manual commands, MCP is working!

## Recommended Next Steps

1. **Today**: Use environment variables (quick fix)
   ```bash
   export SUPABASE_ACCESS_TOKEN="your-token"
   ```

2. **This Week**: Set up MCP servers properly
   - Install npm packages
   - Configure Claude Code settings
   - Test integration

3. **Long-term**: Build custom MCP server for DailyCommit
   - Single command for full deployment
   - Integrated testing and monitoring
   - Automatic rollback on errors

## Security Notes

- ⚠️ Store tokens in environment variables, not in config files committed to git
- ✅ Use token expiration (30-90 days recommended)
- ✅ Scope tokens minimally (only permissions needed)
- ✅ Rotate tokens periodically

## Resources

- MCP Documentation: https://modelcontextprotocol.io/
- GitHub MCP Server: https://github.com/modelcontextprotocol/servers
- Supabase API Docs: https://supabase.com/docs/reference/api
- Claude Code MCP Guide: https://docs.claude.com/claude-code/mcp

---

**Want me to automate deployments now?**

Just set the environment variable:
```bash
export SUPABASE_ACCESS_TOKEN="your-token-here"
```

Then I can run `./deploy_webhook.sh` automatically without prompting!
