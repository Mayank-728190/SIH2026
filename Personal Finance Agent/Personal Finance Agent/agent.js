import readline from 'node:readline/promises';
import { Groq } from 'groq-sdk';
import { agentTools } from './src/tools/agentTools.js';
import { executeTool } from './src/tools/toolHandlers.js';
import dotenv from 'dotenv';

dotenv.config();

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const GROQ_MODELS = [
  'openai/gpt-oss-20b',
  'openai/gpt-oss-120b',
  'groq/compound',
  'groq/compound-mini'
];

async function createChatCompletionWithFallback(params) {
  let lastError = null;
  for (const model of GROQ_MODELS) {
    try {
      const completion = await groq.chat.completions.create({
        ...params,
        model,
      });
      return completion;
    } catch (err) {
      lastError = err;
      const msg = err.message || '';
      if (msg.includes('does not exist') || msg.includes('model_not_found') || msg.includes('decommissioned')) {
        continue;
      }
      throw err;
    }
  }
  throw lastError;
}

async function callAgent() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  
  let currentCustomerId = "CUST_00001";
  console.log("==================================================");
  console.log("Personal Finance AI Agent ('BOT') Initialized");
  console.log(`Active Customer Context: ${currentCustomerId}`);
  console.log("Type 'switch CUST_XXXXX' to change customer context.");
  console.log("Type 'bye' to exit.");
  console.log("==================================================\n");

  while (true) {
    const question = await rl.question("USER: ");

    if (!question || question.trim().toLowerCase() === 'bye') {
      break;
    }

    if (question.trim().startsWith('switch ')) {
      const newId = question.trim().split(' ')[1];
      if (newId) {
        currentCustomerId = newId.toUpperCase();
        console.log(`[Agent] Switched customer context to: ${currentCustomerId}`);
      }
      continue;
    }

    const messages = [
      {
        role: "system",
        content: `You are an AI Assistant, an expert personal finance assistant helping Customer ID: ${currentCustomerId}.
Always fetch real customer data using the provided tools before answering.
Never guess amounts or recommendation scores.
Current Datetime: ${new Date().toUTCString()}`,
      },
      {
        role: "user",
        content: question,
      }
    ];

    let loopCount = 0;
    while (loopCount < 4) {
      loopCount++;
      try {
        const completion = await createChatCompletionWithFallback({
          messages: messages,
          tool_choice: "auto",
          tools: agentTools,
        });

        const choice = completion.choices[0];
        if (!choice) break;

        messages.push(choice.message);
        const toolCalls = choice.message.tool_calls;

        if (!toolCalls || toolCalls.length === 0) {
          console.log(`\nAssistant: ${choice.message.content}\n`);
          break;
        }

        for (const tool of toolCalls) {
          const functionName = tool.function.name;
          const rawArgs = tool.function.arguments || '{}';
          const args = JSON.parse(rawArgs);

          if (!args.customerId) {
            args.customerId = currentCustomerId;
          }

          console.log(`[Tool Call] Executing ${functionName} for customer ${args.customerId}...`);
          const result = await executeTool(functionName, args);

          messages.push({
            role: "tool",
            content: result,
            tool_call_id: tool.id,
          });
        }
      } catch (err) {
        console.error("[Agent Error]", err.message);
        break;
      }
    }
  }
  rl.close();
}

callAgent();
