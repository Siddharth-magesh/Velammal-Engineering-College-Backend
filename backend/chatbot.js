const express = require("express");
const bodyParser = require("body-parser");
const Groq = require("groq-sdk");

const app = express();
app.use(bodyParser.json());

const groq = new Groq({ apiKey: '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' });

async function getGroqChatCompletion(userMessage) {
  return groq.chat.completions.create({
    messages: [
      {
        role: "user",
        content: userMessage,
      },
    ],
    model: "llama-3.3-70b-versatile",
  });
}

app.post("/groq-chat", async (req, res) => {
  const { message } = req.body;

  if (!message) {
    return res.status(400).json({ error: "Message is required in the request body" });
  }

  try {
    const chatCompletion = await getGroqChatCompletion(message);
    const response = chatCompletion.choices[0]?.message?.content || "No response";
    return res.json({ botResponse: response });
  } catch (error) {
    console.error("Error fetching Groq chat completion:", error);
    return res.status(500).json({ error: "Failed to fetch response from Groq API" });
  }
});

const PORT = 5000;
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
