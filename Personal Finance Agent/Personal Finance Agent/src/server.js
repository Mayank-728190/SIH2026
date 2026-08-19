import express from 'express';
import cors from 'cors';
import path from 'node:path';
import dotenv from 'dotenv';
import { Groq } from 'groq-sdk';

import { getAllCustomers, getCustomerById } from './data/customerRepo.js';
import { addTransaction, getRecentTransactions, getCategoryWiseExpenses, getTotalExpense } from './data/transactionRepo.js';
import { getCustomerEvents } from './data/customerEventsRepo.js';
import { getRiskProfile } from './data/riskProfileRepo.js';
import { generateCustomerRecommendations } from './recommendation/recommendationEngine.js';
import { getFullCustomerProfile } from './recommendation/customerProfile.js';
import { agentTools } from './tools/agentTools.js';
import { executeTool } from './tools/toolHandlers.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(process.cwd(), 'src', 'public')));

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

// Models active on Groq endpoint
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
      console.log(`[GroqAttempt] Requesting model '${model}'...`);
      const completion = await groq.chat.completions.create({
        ...params,
        model,
      });
      console.log(`[GroqSuccess] Model '${model}' responded successfully!`);
      return completion;
    } catch (err) {
      lastError = err;
      const msg = err.message || '';
      console.warn(`[GroqModelFallback] Model '${model}' failed: ${msg}. Trying next model...`);
      continue;
    }
  }
  throw lastError;
}

// Deterministic Data Engine Fallback if API fails
function generateFallbackChatResponse(customerId, userMessage) {
  const fullProfile = getFullCustomerProfile(customerId);
  const recs = generateCustomerRecommendations(customerId);
  if (!fullProfile || !fullProfile.customer) {
    return `Hello! I could not retrieve profile records for customer ID ${customerId}.`;
  }

  const cust = fullProfile.customer;
  const lowerMsg = userMessage.toLowerCase();

  if (lowerMsg.includes('spend') || lowerMsg.includes('expense') || lowerMsg.includes('cost') || lowerMsg.includes('food') || lowerMsg.includes('shopping')) {
    const total = fullProfile.behavior.dynamicTotalSpend;
    const topCat = fullProfile.behavior.topCategory;
    const cats = fullProfile.behavior.sortedCategories.slice(0, 3).map(c => `• **${c.category}**: ₹${c.amount.toLocaleString()}`).join('\n');
    return `Here is your spending analysis for **${cust.Full_Name}** (${customerId}):\n\n- **Total Monthly Spend**: ₹${total.toLocaleString()}\n- **Top Category**: ${topCat}\n\n**Category Breakdown**:\n${cats}`;
  }

  if (lowerMsg.includes('recommend') || lowerMsg.includes('why') || lowerMsg.includes('card') || lowerMsg.includes('offer') || lowerMsg.includes('product')) {
    const topP = recs.topProducts[0];
    const topO = recs.topOffers[0];
    let reply = `Here are your personalized recommendations for **${cust.Full_Name}**:\n\n`;
    if (topP) {
      reply += `1. **${topP.name}** (${topP.type}) - Score: **${topP.score}/100**\n   - *Why*: ${topP.explanation.reasons.slice(0, 2).join(' ')}\n\n`;
    }
    if (topO) {
      reply += `2. **${topO.name}** (${topO.category} Offer) - Score: **${topO.score}/100**\n   - *Why*: ${topO.explanation.reasons.slice(0, 2).join(' ')}\n\n`;
    }
    reply += `*Baseline Next Best Action*: ${recs.baseline.nextBestAction || 'Maintain low debt ratio'}.`;
    return reply;
  }

  if (lowerMsg.includes('cibil') || lowerMsg.includes('income') || lowerMsg.includes('score') || lowerMsg.includes('risk') || lowerMsg.includes('profile')) {
    return `Here is your financial profile summary for **${cust.Full_Name}**:\n- **CIBIL Score**: ${cust.CIBIL_Score}\n- **Monthly Income**: ₹${cust.Monthly_Income.toLocaleString()}\n- **Savings Ratio**: ${(cust.Savings_Ratio * 100).toFixed(0)}%\n- **Risk Status**: ${fullProfile.riskProfile?.Fraud_Flag ? 'High Risk Flagged' : 'Low / Good Standing'}`;
  }

  return `Hello **${cust.Full_Name}**! I have reviewed your account data (${customerId}). Your total spend is **₹${fullProfile.behavior.dynamicTotalSpend.toLocaleString()}** (top category: ${fullProfile.behavior.topCategory}). You have **${recs.topProducts.length}** recommended products and **${recs.topOffers.length}** eligible offers available on your dashboard.`;
}

// 0. Customer Login Authentication API
app.post('/api/login', (req, res) => {
  try {
    const { customerId, password } = req.body;
    if (!customerId || !password) {
      return res.status(400).json({ success: false, error: 'Customer ID and Password are required.' });
    }
    if (password !== '1234') {
      return res.status(401).json({ success: false, error: 'Invalid Password. Password for all users is 1234.' });
    }
    const customer = getCustomerById(customerId);
    if (!customer) {
      return res.status(404).json({ success: false, error: `Customer ID "${customerId}" not found.` });
    }
    res.json({ success: true, customerId, customer });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 1. Customer Login / List API
app.get('/api/customers', (req, res) => {
  try {
    const customers = getAllCustomers(100);
    res.json({ success: true, customers });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 2. Personalized Dashboard Data API
app.get('/api/customer/:id/dashboard', (req, res) => {
  try {
    const customerId = req.params.id;
    const fullProfile = getFullCustomerProfile(customerId);
    if (!fullProfile) {
      return res.status(404).json({ success: false, error: `Customer ${customerId} not found` });
    }

    const recentTxns = getRecentTransactions(customerId, 15);
    const recentEvents = getCustomerEvents(customerId).slice(-10).reverse();
    const recommendations = generateCustomerRecommendations(customerId);

    res.json({
      success: true,
      customerId,
      customer: fullProfile.customer,
      riskProfile: fullProfile.riskProfile,
      behavior: fullProfile.behavior,
      recentTransactions: recentTxns,
      recentEvents,
      recommendations,
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 3. Submit Transaction API (Appends to transactions.csv & recalculates)
app.post('/api/transactions', (req, res) => {
  try {
    const {
      Customer_ID,
      Transaction_Amount,
      Merchant_Name,
      Merchant_Category,
      Transaction_Channel,
      Transaction_Date,
      Transaction_Location
    } = req.body;

    if (!Customer_ID) {
      return res.status(400).json({ success: false, error: 'Customer_ID is required.' });
    }

    const amount = Number(Transaction_Amount);
    if (isNaN(amount) || amount <= 0) {
      return res.status(400).json({ success: false, error: 'Amount must be a positive number.' });
    }

    // Append to transactions.csv & update cache
    const newTxn = addTransaction({
      Customer_ID,
      Transaction_Amount: amount,
      Merchant_Name: Merchant_Name || 'Merchant Store',
      Merchant_Category: Merchant_Category || 'Shopping',
      Transaction_Channel: Transaction_Channel || 'UPI',
      Transaction_Date: Transaction_Date || new Date().toISOString().split('T')[0],
      Transaction_Location: Transaction_Location || 'Local Store'
    });

    // Recalculate dynamic recommendations and dashboard stats
    const updatedRecommendations = generateCustomerRecommendations(Customer_ID);
    const updatedProfile = getFullCustomerProfile(Customer_ID);

    res.json({
      success: true,
      message: 'Transaction successfully appended to transactions.csv',
      transaction: newTxn,
      updatedBehavior: updatedProfile.behavior,
      updatedRecommendations,
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 4. AI Chat Integration API with Tool Execution & Guaranteed Fallback
app.post('/api/chat', async (req, res) => {
  try {
    const { customerId, message, conversationHistory = [] } = req.body;

    if (!customerId || !message) {
      return res.status(400).json({ success: false, error: 'customerId and message are required.' });
    }

    const fullProfile = getFullCustomerProfile(customerId);
    const custName = fullProfile?.customer?.Full_Name || customerId;

    const systemPrompt = {
      role: 'system',
      content: `You are Josh, a personal finance assistant helping Customer ID: ${customerId} (${custName}).
Available customer data: CIBIL Score = ${fullProfile?.customer?.CIBIL_Score}, Monthly Income = ₹${fullProfile?.customer?.Monthly_Income}, Total Spend = ₹${fullProfile?.behavior?.dynamicTotalSpend}.
Always invoke tool functions (getCustomerProfile, getTransactions, getCategoryWiseExpenses, getRecommendations, getRecommendationReason) to fetch exact customer data.
Never guess amounts or scores.`,
    };

    const messages = [systemPrompt];
    for (const msg of conversationHistory) {
      if (msg.role && msg.content) {
        messages.push({ role: msg.role, content: msg.content });
      }
    }

    messages.push({ role: 'user', content: message });

    const toolExecutionLogs = [];

    try {
      let loopCount = 0;
      while (loopCount < 4) {
        loopCount++;
        const completion = await createChatCompletionWithFallback({
          messages,
          tool_choice: 'auto',
          tools: agentTools,
        });

        const choice = completion.choices[0];
        if (!choice) break;

        messages.push(choice.message);
        const toolCalls = choice.message.tool_calls;

        if (!toolCalls || toolCalls.length === 0) {
          const finalReply = choice.message.content || generateFallbackChatResponse(customerId, message);
          return res.json({
            success: true,
            reply: finalReply,
            toolLogs: toolExecutionLogs,
          });
        }

        for (const tool of toolCalls) {
          const functionName = tool.function.name;
          const rawArgs = tool.function.arguments || '{}';
          const args = JSON.parse(rawArgs);

          if (!args.customerId) {
            args.customerId = customerId;
          }

          toolExecutionLogs.push({ tool: functionName, args });
          console.log(`[Server AI Tool] Executing ${functionName} for ${args.customerId}...`);

          const result = await executeTool(functionName, args);

          messages.push({
            role: 'tool',
            content: result,
            tool_call_id: tool.id,
          });
        }
      }

      return res.json({
        success: true,
        reply: messages[messages.length - 1]?.content || generateFallbackChatResponse(customerId, message),
        toolLogs: toolExecutionLogs,
      });

    } catch (llmError) {
      console.warn('[Server LLM Warning] LLM call failed, engaging deterministic data engine fallback:', llmError.message);
      const fallbackReply = generateFallbackChatResponse(customerId, message);
      return res.json({
        success: true,
        reply: fallbackReply,
        toolLogs: [{ tool: 'executeDataEngineFallback', args: { customerId } }],
      });
    }

  } catch (err) {
    console.error('[API Chat Error]', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`==================================================`);
  console.log(`Personal Finance Recommendation Server running!`);
  console.log(`Web Dashboard URL: http://localhost:${PORT}`);
  console.log(`==================================================`);
});
