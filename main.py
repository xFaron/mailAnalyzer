import os.path
import base64

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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

        elif "image" in content_type.lower():
          #TODO <-- get the image in base64 encoded format. LLMs can take that as input
          pass

        msg['body'].append({
          "type": content_type,
          "data": decoded_string,
          "filename": payload['filename']
        })


    return (msgId, threadId, msg)
  
  @staticmethod
  def extract_payloads(top_level_payload, returnList = []):
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
      pass
    else:
      print("No message Id was passed during initialization")


class Thread:
  def __init__(self, gmail_thread_obj):
    self.id = None
    self.msgs = []

    if gmail_thread_obj:
      self.id, self.msgs = Thread.parse(gmail_thread_obj)

  @staticmethod
  def parse(gmail_thread_obj):
    threadId = gmail_thread_obj['id']
    messages = [Msg(msg) for msg in gmail_thread_obj['messages']]

    return threadId, messages

  def retrieve_latest(self):
    if self.id:
      pass
    else:
      print("No thread Id was passed during initialization")


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    # Init API
    api = Gmail_API()
    messages = []

    # Get message Id's
    results = api.service.users().messages().list(userId="me").execute()
    messagesIds = results.get("messages", [])

    #print(f"ThreadIds are", "Distinct" if len(list(map(lambda x: x['threadId'], messagesIds))) == len(set(map(lambda x: x['threadId'], messagesIds))) else "Not Distinct")

    if not messagesIds:
      print("No message_Ids found.")
      return

    # Get the messages
    for id_ in messagesIds:
      result = api.service.users().messages().get(userId="me", id=id_["id"]).execute()
      #print(result["snippet"])
      messages.append(Msg(result))

    for msg_obj in messages:
      print(str(msg_obj.msg['body'][0]["data"]))

if __name__ == "__main__":
  main()