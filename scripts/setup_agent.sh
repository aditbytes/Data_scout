#!/bin/bash
# =============================================================================
# DataScout — Bedrock Agent Setup Script
# =============================================================================
# Creates and configures the Amazon Bedrock Agent with Code Interpreter.
# Idempotent — safe to re-run.
# =============================================================================
set -euo pipefail
export AWS_PAGER=""

AGENT_NAME="DataScout-Analyst"
MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/DataScout-BedrockAgentRole"

echo "═══════════════════════════════════════════════════════"
echo " DataScout — Bedrock Agent Setup"
echo "═══════════════════════════════════════════════════════"

# Agent instructions
INSTRUCTIONS="You are DataScout, an autonomous enterprise data analyst AI. Your primary role is to help users analyze datasets by writing and executing Python code.

CRITICAL RULES:
1. NEVER guess or hallucinate numerical values -- ALL numbers must come from code execution
2. ALWAYS use the Code Interpreter to compute results
3. Generate clean, readable Python code using pandas and numpy
4. Include error handling in all generated code
5. Explain your analytical approach clearly
6. Show all code to the user for full transparency

WORKFLOW:
1. Understand the user analytical question
2. Plan the analysis steps
3. Write Python code to perform the analysis
4. Execute the code using Code Interpreter
5. Validate the results (check for nulls, errors)
6. Create visualizations if they add value
7. Present results with clear explanations

AVAILABLE LIBRARIES: pandas, numpy, matplotlib, seaborn, scipy, scikit-learn

RESPONSE FORMAT:
1. Brief explanation of analysis approach
2. Generated Python code (in code block)
3. Results (tables, statistics, insights)
4. Visualizations (if created)
5. Summary and next steps"

# Create agent
echo "→ Creating Bedrock Agent..."
AGENT_ID=$(aws bedrock-agent create-agent \
    --agent-name "$AGENT_NAME" \
    --foundation-model "$MODEL_ID" \
    --instruction "$INSTRUCTIONS" \
    --agent-resource-role-arn "$ROLE_ARN" \
    --idle-session-ttl-in-seconds 600 \
    --query 'agent.agentId' --output text 2>/dev/null || echo "EXISTS")

if [ "$AGENT_ID" = "EXISTS" ]; then
    echo "  Agent already exists. Looking up ID..."
    AGENT_ID=$(aws bedrock-agent list-agents \
        --query "agentSummaries[?agentName=='${AGENT_NAME}'].agentId" \
        --output text)
fi

echo "  Agent ID: $AGENT_ID"

# Prepare agent
echo "→ Preparing agent..."
aws bedrock-agent prepare-agent --agent-id "$AGENT_ID"
echo "  Agent prepared."

# Create production alias
echo "→ Creating production alias..."
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
    --agent-id "$AGENT_ID" \
    --agent-alias-name PRODUCTION \
    --query 'agentAlias.agentAliasId' --output text 2>/dev/null || echo "EXISTS")

if [ "$ALIAS_ID" = "EXISTS" ]; then
    ALIAS_ID=$(aws bedrock-agent list-agent-aliases \
        --agent-id "$AGENT_ID" \
        --query "agentAliasSummaries[?agentAliasName=='PRODUCTION'].agentAliasId" \
        --output text)
fi

echo "  Alias ID: $ALIAS_ID"

echo ""
echo "═══════════════════════════════════════════════════════"
echo " ✅ Setup Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo " Add these to your .env file:"
echo "  BEDROCK_AGENT_ID=$AGENT_ID"
echo "  BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID"
echo ""
