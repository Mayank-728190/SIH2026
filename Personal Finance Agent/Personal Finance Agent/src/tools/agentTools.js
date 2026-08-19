export const agentTools = [
  {
    type: "function",
    function: {
      name: "getCustomerProfile",
      description: "Get full profile, income, CIBIL, segment, and financial attributes of a customer.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getTransactions",
      description: "Get all recorded transactions for a customer.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" },
          limit: { type: "number", description: "Optional max number of transactions to return" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getRecentTransactions",
      description: "Get the most recent transactions for a customer.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" },
          count: { type: "number", description: "Number of recent transactions to return (default 10)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getTotalExpense",
      description: "Get total expense in INR for a customer between optional from and to dates.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" },
          from: { type: "string", description: "From date in YYYY-MM-DD format" },
          to: { type: "string", description: "To date in YYYY-MM-DD format" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getCategoryWiseExpenses",
      description: "Get total expense breakdown grouped by category (Grocery, Food, Travel, etc.) for a customer.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getCustomerEvents",
      description: "Get customer interaction events such as offer views, clicks, and redemptions.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getRiskProfile",
      description: "Get security and risk indicators for a customer including fraud score and login flags.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getEligibleProducts",
      description: "Get list of financial products for which the customer meets eligibility requirements.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getRecommendations",
      description: "Get top personalized product and offer recommendations with scores for a customer.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" }
        },
        required: ["customerId"]
      }
    }
  },
  {
    type: "function",
    function: {
      name: "getRecommendationReason",
      description: "Get detailed factual data-backed explanation for why a specific product or offer was recommended.",
      parameters: {
        type: "object",
        properties: {
          customerId: { type: "string", description: "Customer ID (e.g. CUST_00001)" },
          itemId: { type: "string", description: "Product ID or Offer ID (e.g. PROD_001 or OFFER_001)" }
        },
        required: ["customerId"]
      }
    }
  }
];
