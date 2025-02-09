# **Prompt: Summarize an Email in One Sentence**
## **Context:**  
You will be provided with a Python dictionary containing structured email data. Your task is to generate a **very small summary** (one sentence) that captures the key point of the email.  

## **Instructions:**  
- The email data will be structured as follows:  
  ```json
  {
    "subject": "Meeting Reminder",
    "from": "alice@example.com",
    "to": "bob@example.com",
    "date": "Mon, 05 Feb 2024 10:30:00 +0000",
    "body": [
      {
        "type": "text/plain",
        "data": "Hi Bob, just a reminder about our meeting at 2 PM.",
        "filename": ""
      }
    ]
  }
  ```
- Extract the **most important** information from the **subject and body**.
- **Do not include sender/receiver names or unnecessary details.**
- Summarize the email **in one concise sentence** (no longer than 20 words).
- If the body contains multiple sections, summarize only the **core idea**.
- Avoid generic statements like *"This is an email."* or *"This email is about something important."*  

## **Example Output:**  
For the given input, your response should be:  
📝 **"Reminder about a scheduled meeting at 2 PM."**  

# **Input**

