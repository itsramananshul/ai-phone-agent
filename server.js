require("dotenv").config();
const express = require("express");
const app = express();
app.use(express.urlencoded({ extended: false }));
app.use("/static", express.static("static"));
// Store ready audio files here
const pendingReplies = {};

// Called by Python when AI reply is ready
app.post("/ai-ready", express.json(), (req, res) => {
  const { callSid, audioUrl } = req.body;
  console.log("AI reply ready for call:", callSid);
  pendingReplies[callSid] = audioUrl;
  res.sendStatus(200);
});

app.post("/voice", (req, res) => {
  const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">Hi! I am an AI assistant. Please speak after the beep.</Say>
  <Record
    maxLength="15"
    action="/handle-recording"
    playBeep="true"
    recordingStatusCallback="/handle-recording-done"
  />
</Response>`;
  res.type("text/xml");
  res.send(twiml);
});

app.post("/handle-recording", (req, res) => {
  const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">Got it, one moment...</Say>
  <Redirect>/wait-for-reply</Redirect>
</Response>`;
  res.type("text/xml");
  res.send(twiml);
});

// Keep checking if AI reply is ready every 5 seconds
app.post("/wait-for-reply", (req, res) => {
  const callSid = req.body.CallSid;
  
  if (pendingReplies[callSid]) {
    // AI is ready! Play the reply
    const audioUrl = pendingReplies[callSid];
    delete pendingReplies[callSid];
    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Play>${audioUrl}</Play>
  <Record
    maxLength="15"
    action="/handle-recording"
    playBeep="true"
    recordingStatusCallback="/handle-recording-done"
  />
</Response>`;
    res.type("text/xml");
    res.send(twiml);
  } else {
    // Still waiting, check again in 5 seconds
    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Pause length="5"/>
  <Redirect>/wait-for-reply</Redirect>
</Response>`;
    res.type("text/xml");
    res.send(twiml);
  }
});

// Forward recording callback to Python
app.post("/handle-recording-done", async (req, res) => {
  console.log("Recording done, forwarding to Python...");
  try {
    const response = await fetch("http://127.0.0.1:5001/handle-recording-done", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(req.body).toString()
    });
    console.log("Python responded:", response.status);
  } catch (err) {
    console.error("Error forwarding to Python:", err.message);
  }
  res.sendStatus(200);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));