# DataScout — Amazon Bedrock Agent Deployment Checklist

This guide covers the exact steps required to deploy the DataScout Bedrock Agent (Claude 3.5 Sonnet) from scratch, ensuring all IAM permissions, Inference Profiles, and Aliases are correctly configured so the Streamlit app can communicate with it without `accessDeniedException` or `validationException` errors.

---

## Phase 1: Enable Model Access
Before creating the agent, you must ensure your AWS account has access to the Claude foundation models.

- [ ] **1.1. Go to Amazon Bedrock** in the AWS Console (ensure you are in `us-east-1` region).
- [ ] **1.2. Navigate to "Model access"** in the left sidebar (under "Configure and learn").
- [ ] **1.3. Click "Enable all models"** or click "Modify model access".
- [ ] **1.4. Request access for Anthropic models:** Select **Claude 3.5 Sonnet** and **Claude 3.5 Sonnet v2**.
- [ ] **1.5. Submit Use Case Details (First-time only):** Fill out the Anthropic use case form (Company, Website, Industry, Internal Users, and a brief description like "Enterprise data analysis tool").
- [ ] **1.6. Verify Access:** Wait a few minutes and confirm the status says **Access granted**.

---

## Phase 2: Create the Bedrock Agent
Create the agent that will process the data analysis queries.

- [ ] **2.1. Go to "Agents"** in the Bedrock left sidebar and click "Create Agent".
- [ ] **2.2. Name the agent:** `DataScout-Analyst` (or similar).
- [ ] **2.3. Agent Resource Role:** Select "Create and use a new service role" (AWS will create `AmazonBedrockExecutionRoleForAgents_...`). *Note: If you already have `DataScout-BedrockAgentRole`, you can select "Use an existing service role".*
- [ ] **2.4. Select Model:** Choose **Claude 3.5 Sonnet v2** (or v1).
    - *Crucial Step:* Look at the "Inference" panel on the right side. Select the **Cross-region Inference Profile** (e.g., `US Anthropic Claude 3.5 Sonnet v2`). Do *not* select the base model ID directly if it is labeled "Legacy" or throws a validation error on-demand.
- [ ] **2.5. Instructions:** Add the system prompt/instructions for how the Data Analyst should behave.
- [ ] **2.6. Additional Settings:** Enable **Code Interpreter** (required for data analysis and generating charts).
- [ ] **2.7. Save:** Click "Save" at the top.

---

## Phase 3: Configure Agent IAM Role Permissions (The Fix for Access Denied)
The role the *Agent* uses to execute needs permission to invoke the Claude Inference Profile.

- [ ] **3.1. Open IAM Console** in a new tab.
- [ ] **3.2. Go to "Roles"**.
- [ ] **3.3. Search for your Agent's Role.** This is either `DataScout-BedrockAgentRole` (if you used an existing one) or the auto-generated role starting with `AmazonBedrockExecutionRoleForAgents_...`.
- [ ] **3.4. Click the Role name.**
- [ ] **3.5. Add Permissions:** Click "Add permissions" -> "Create inline policy".
- [ ] **3.6. Switch to JSON tab** and paste the following policy to allow the agent to use the models and inference profiles:
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "bedrock:InvokeModel",
          "Resource": [
            "arn:aws:bedrock:us-east-1::foundation-model/*",
            "arn:aws:bedrock:us-east-1:*:inference-profile/*"
          ]
        }
      ]
    }
    ```
- [ ] **3.7. Save Policy:** Name it `BedrockInferenceProfileAccess` and click "Create policy".

---

## Phase 4: Prepare and Deploy the Agent (The Fix for Streamlit Sync)
Streamlit apps connect to a specific "Alias" of the agent. An Alias is locked to a specific "Version". You must link your new fixes to the Alias.

- [ ] **4.1. Go back to Bedrock Console -> Agents -> your Agent.**
- [ ] **4.2. Prepare:** Click the **Prepare** button at the top right. Wait for the green success banner. (This packages your current working draft).
- [ ] **4.3. Scroll down to Aliases.** Look for your aliases (e.g., `PRODUCTION`).
- [ ] **4.4. Edit the Alias:** Select the radio button next to `PRODUCTION` and click **Edit**.
- [ ] **4.5. Update Version:** Change the "Associated version" dropdown from the old version (e.g., Version 1) to **Create a new version**.
- [ ] **4.6. Save:** Click **Save and exit**. AWS will create a new version (e.g., Version 2) of your agent (which includes all the IAM and model fixes) and point the `PRODUCTION` alias to it.

---

## Phase 5: Configure the Streamlit App (.env)
Finally, ensure your code has the correct credentials and IDs.

- [ ] **5.1. IAM User Permissions:** The IAM User powering the Streamlit App (e.g., `datascout-developer` via Access Keys) must have permission to invoke the AWS Agent. Ensure the user has the `AmazonBedrockFullAccess` managed policy, or a custom policy allowing `bedrock:InvokeAgent`.
- [ ] **5.2. Get IDs:** From the Agent details page, copy the **Agent ID** (e.g., `2V8KLCC97S`) and the **Alias ID** for `PRODUCTION` (e.g., `GZJRYQRXYI`).
- [ ] **5.3. Update `.env`:** Open the `.env` file in your DataScout project root and ensure they match:
    ```env
    AWS_REGION=us-east-1
    BEDROCK_AGENT_ID=2V8KLCC97S
    BEDROCK_AGENT_ALIAS_ID=GZJRYQRXYI
    ```
- [ ] **5.4. Restart App:** In your terminal, stop the app (`Ctrl+C`) and run:
    ```bash
    streamlit run streamlit_app/app.py
    ```

**You should now be able to upload datasets and ask questions without any access errors!**
