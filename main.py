import os.path
import base64
from datetime import datetime

from google import genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

debug = False

class Gmail_API:
  def __init__(self):
    self.creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
      self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not self.creds or not self.creds.valid:
      if self.creds and self.creds.expired and self.creds.refresh_token:
        self.creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        self.creds = flow.run_local_server(port=0)
      # Save the credentials for the next run
      with open("token.json", "w") as token:
        token.write(self.creds.to_json())

    try:
      # Init API
      self.service = build("gmail", "v1", credentials=self.creds) 
    except HttpError as error:
      print(f"An error occurred: {error}")


class Msg:
  def __init__ (self, gmail_msg_obj = None):
    self.id = None
    self.threadId = None
    self.msg = {}

    if gmail_msg_obj:
      self.id, self.threadId, self.msg = Msg.parse(gmail_msg_obj)

  @staticmethod
  def parse(gmail_msg_obj):
    msg = {}
    msgId = gmail_msg_obj['id']
    threadId = gmail_msg_obj['threadId']

    # Getting labels
    msg['labels'] = gmail_msg_obj['labelIds']
    msg['body'] = []

    # Getting headers
    for hearderVals in gmail_msg_obj['payload']['headers']:
      if hearderVals['name'].lower() in ["subject", "from", "to", "date"]:
        msg[hearderVals['name'].lower()] = hearderVals['value']

    payloads = Msg.extract_payloads(gmail_msg_obj['payload'])

    for payload in payloads:
      content_type = None

      for header in payload['headers']:
        if header['name'] == "Content-Type":
          content_type = header['value']

      if content_type:
        if "text/plain" in content_type.lower():
          raw_string = payload['body']['data']
          byte_string = base64.urlsafe_b64decode(raw_string)
          decoded_string = byte_string.decode("utf-8")

        # elif "image" in content_type.lower():
        #   #TODO <-- get the image in base64 encoded format. LLMs can take that as input
        #   pass

          msg['body'].append({
            "type": content_type,
            "data": decoded_string,
            "filename": payload['filename']
          })


    return (msgId, threadId, msg.copy())
  
  @staticmethod
  def extract_payloads(top_level_payload, returnList = None):
    if returnList is None:
      returnList = []

    try:
      parts = top_level_payload['parts']
      for part in parts:
        returnList = Msg.extract_payloads(part, returnList)
    except KeyError:
      payloads = top_level_payload
      returnList.append(payloads)
    
    return returnList

  def extract_date(self):
    if self.id:
      try:
        date_string = self.msg['date']
        msg_date = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        return msg_date
      except:
        print("No associated date found")
    else:
      print("No message Id was passed during initialization")
    
    return None


class Thread:
  def __init__(self, gmail_thread_obj):
    self.id = None
    self.msgs = []

    if gmail_thread_obj:
      self.id, self.msgs = Thread.parse(gmail_thread_obj)

  @staticmethod
  def parse(gmail_thread_obj):
    messages = {}

    threadId = gmail_thread_obj['id']
    messages = [Msg(msg) for msg in gmail_thread_obj['messages']]

    return threadId, messages

  def retrieve_latest(self):
    if self.id:
      req_message = self.msgs[0]
      for msg in self.msgs[1:]:
        if req_message.extract_date() < msg.extract_date():
          req_message = msg

      return req_message
    else:
      print("No thread Id was passed during initialization")


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def retrieveEmails(api) :
  messages = []

  results = api.service.users().threads().list(userId="me", labelIds=["INBOX", "UNREAD"]).execute()
  threadIds = results.get("threads", [])

  if not threadIds:
    print("No threads found.")
    return

  for id_ in threadIds:
    result = api.service.users().threads().get(userId="me", id=id_["id"]).execute()
    tempThread = Thread(result)
    messages.append(tempThread.retrieve_latest())

  return messages

def main():
  # Init API
  print("Starting API")
  api = Gmail_API()
  client = None
  with open("key.txt") as file:
    client = genai.Client(api_key=f"{file.read()}")

  # Retrieve Unread Emails
  print("Retrieving Unread mails")
  messages = retrieveEmails(api)

  print("Summarizing")
  with open('prompt1.md') as file:
    prompt = file.read()

    for msg_obj in messages:
      response = client.models.generate_content(
          model="gemini-2.0-flash-thinking-exp-01-21", contents=f"{prompt}\n{msg_obj.msg}"
      )
      print(response.text)
    
if __name__ == "__main__":
  main()