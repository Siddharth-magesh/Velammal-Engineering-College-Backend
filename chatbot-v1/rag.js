const express = require("express");
const bodyParser = require("body-parser");
const { Pinecone } = require("@pinecone-database/pinecone");
const Groq = require("groq-sdk");
const axios = require("axios");

const app = express();
const port = 3000;

app.use(bodyParser.json());

const pineconeApiKey = 'pcsk_5XXpmL_TJeSzwPSbUNL1i33viwUUugZwqnkVUQd6ZzpmMcQmEsZiS1pR64jWX9oGw1sFzR';
const indexHost = 'https://vec-data-mkz5a3h.svc.aped-4627-b74a.pinecone.io';
const indexName = "vec-data"; 
const groqApiKey = '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';

const pinecone = new Pinecone({ apiKey: pineconeApiKey });
const groq = new Groq({ apiKey: groqApiKey });

app.post("/rag", async (req, res) => {
  console.log("Incoming request to /rag endpoint.");
  console.log("Request body:", req.body);

  try {
    const { query } = req.body;

    if (!query) {
      console.error("Query is missing in the request body.");
      return res.status(400).json({ error: "Query is required." });
    }

    console.log("Initializing Pinecone index...");
    const index = pinecone.Index(indexName);

    console.log("Generating query embedding...");
    const embeddingModel = "all-MiniLM-L6-v2";
    let queryEmbedding;

    try {
      queryEmbedding = await generateEmbedding(query, embeddingModel);
      console.log("Generated query embedding:", queryEmbedding);
    } catch (error) {
      console.error("Error generating query embedding:", error.message);
      return res.status(500).json({ error: "Failed to generate query embedding." });
    }

    console.log("Querying Pinecone index...");
    let queryResponse;
    try {
      queryResponse = await index.query({
        vector: queryEmbedding,
        topK: 10,
        includeValues: true,
        includeMetadata: true,
      });
      console.log("Pinecone query response:", queryResponse);
    } catch (error) {
      console.error("Error querying Pinecone index:", error.message);
      return res.status(500).json({ error: "Failed to query Pinecone index." });
    }

    const results = queryResponse.matches.map((match) => ({
      metadata: match.metadata,
      score: match.score,
    }));

    console.log("Query results:", results);

    console.log("Generating context for LLM...");
    const context = results
      .map((result) => result.metadata.collection)
      .join("\n");
    console.log("Generated context:", context);

    console.log("Sending context to Groq LLM...");
    let chatCompletion;
    try {
      chatCompletion = await groq.chat.completions.create({
        messages: [
          {
            role: "user",
            content: `Context: ${context}\n\nUser Query: ${query}`,
          },
        ],
        model: "llama-3.3-70b-versatile",
      });
      console.log("Groq LLM response:", chatCompletion);
    } catch (error) {
      console.error("Error processing Groq LLM request:", error.message);
      return res.status(500).json({ error: "Failed to process LLM request." });
    }

    const llmResponse = chatCompletion.choices[0]?.message?.content || "";

    console.log("Final LLM response:", llmResponse);

    res.json({
      query,
      results,
      response: llmResponse,
    });
  } catch (error) {
    console.error("Unhandled error processing RAG request:", error.message);
    res.status(500).json({ error: "Failed to process request." });
  }
});

const generateEmbedding = async (text, modelName) => {
    console.log("Generating embedding for text:", text);
    try {
      const response = await axios.post("http://localhost:5000/generate_embedding", {
        text,
      });
      console.log("Embedding generation response:", response.data);
      return response.data.embedding;
    } catch (error) {
      console.error("Error generating embedding:", error.message);
      throw new Error("Embedding generation failed.");
    }
};

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});
