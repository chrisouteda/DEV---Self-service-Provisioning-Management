import json, os, boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests

def send_email(recipient, subject, body,body_html):
   # This address must be verified with Amazon SES.
   SENDER = "couteda@denodo.com"
 
   # If your account is still in the sandbox, this address must be verified.
   RECIPIENT = recipient
 
   # Specify a configuration set. If you do not want to use a configuration
   # set, comment the following variable, and the 
   # ConfigurationSetName=CONFIGURATION_SET argument below.
   # CONFIGURATION_SET = "ConfigSet"
 
   # The AWS Region you're using for Amazon SES.
   AWS_REGION = "us-east-1"
 
   # The subject line for the email.
   SUBJECT = subject
 
   # The email body for recipients with non-HTML email clients.
   BODY_TEXT = body
             
   # The HTML body of the email.
   #BODY_HTML = """<html> <head></head> <body> <h1>Amazon SES Test (SDK for Python)</h1> <p>This email was sent with <a href='https://aws.amazon.com/ses/'> Amazon SES </a> using <a href='https://aws.amazon.com/sdk-for-python/'> AWS SDK for Python (Boto)</a>.</p> </body> </html>"""            
   BODY_HTML = body_html
   # The character encoding for the email.
   CHARSET = "UTF-8"
 
   # Create a new SES resource and specify a region.
   client = boto3.client('ses',region_name=AWS_REGION)
 
   # Try to send the email.
   try:
       #Provide the contents of the email.
       response = client.send_email(
           Destination={
               'ToAddresses': [
                   RECIPIENT,
               ],
           },
           Message={
               'Body': {
                   'Html': {
                       'Charset': CHARSET,
                       'Data': BODY_HTML,
                   },
                   'Text': {
                       'Charset': CHARSET,
                       'Data': BODY_TEXT,
                   },
               },
               'Subject': {
                   'Charset': CHARSET,
                   'Data': SUBJECT,
               },
           },
           Source=SENDER,
           # If you are not using a configuration set, comment or delete the
           # following line
           # ConfigurationSetName=CONFIGURATION_SET,
     )
   # Display an error if something goes wrong. 
   except ClientError as e:
       print(e.response['Error']['Message'])
       return(e.response['Error']['Message'])
   else:
       print("Email sent! Message ID:" + response['MessageId'] )
       return("Email sent! Message ID:" + response['MessageId'] )


def lambda_handler(event, context):
    print('Event:', json.dumps(event))
    print('Context:', str(context))
    # Switch between the two blocks of code to run
    # This is normally in separate functions
    completeExecutionId = event['executionId']
    executionId = completeExecutionId[-36:]
    print(executionId)
    if event['step'] == 'Send Approval Request':
        #sendArn = os.environ['MANAGER_TOPIC_ARN']
        print('Calling sfn-callback-urls app')
        input = {
            # Step Functions gives us this callback token
            # sfn-callback-urls needs it to be able to complete the task
            "token": event['token'],
            "actions": [
                # The approval action that transfers the name to the output
                {
                    "name": "approve",
                    "type": "success",
                    "output": {
                        # watch for re-use of this field below
                        "name_in_output": event['name_in_input']
                    }
                },
                # The rejection action that names the rejecter
                {
                    "name": "reject",
                    "type": "failure",
                    "error": "rejected",
                    "cause": event['name_in_input'] + " rejected it"
                },
                {
                    "name": "reject_with_comments",
                    "type": "post",
                    "outcomes": [
                        {
                        "name": "reject_with_comments",
                        "type": "failure",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "comment": {
                                    "type": "string"
                                }
                            },
                            "required": ["comment"]
                        },
                        "error": "rejected_with_message",
                        "cause_path": "$.comment"
                        }
                    ]
                }
            ]
        }
        print('payload: ' + json.dumps(input))
        response = boto3.client('lambda').invoke(
            FunctionName=os.environ['CREATE_URLS_FUNCTION'],
            Payload=json.dumps(input)
        )
        #print('response: ' + json.dumps(json.loads(response['Payload'].read())))
        #print('response: ' + json.loads(response['Payload'].read())['message'])
        urls = json.loads(response['Payload'].read())['urls']
        print('Got urls:', urls)

        # Compose email
        email_subject = '[DAPS] Action Required: Approval Request from ' + event['name_in_input'].split("@")[0] + ' [Id: ' + executionId + ']'

        email_body = """
        Hello Manager,
        Select to Approve or Reject the following request from {email}:
        {Frequest}
        Opportunity - {Fopportunity}
        
        Details:
        Service: {Fservice}
        Public IP: {Fpublicip}
        Time Start: {Ftimestart}
        Time End: {Ftimeend}

        Approve:
        {approve}

        Reject:
        {reject}
        
        This email was automatically sent by:
        Denodo Automated Provisioning System (DAPS)
        """.format(
            email=event['name_in_input'],
            name=event['name_in_input'].split("@")[0],
            approve=urls['approve'],
            reject=urls['reject'],
            Fservice=event['Fservice'],
            Fpublicip=event['Fpublicip'],
            Ftimestart=event['Ftimestart'],
            Ftimeend=event['Ftimeend'],
            Frequest=event['Frequest'],
            Fopportunity=event['Fopportunity']
        )
        # html body
        email_body1 = """
        <html>
            <head></head>
            <body>
                <br>Hello Manager,</br>
                <br>Select to Approve or Reject the following request from {email}:</br>
                <br>{Frequest}</br>
                <br>Opportunity - {Fopportunity}</br>
                <br></br>
                <br>Details:</br>
                <br>Service: {Fservice}</br>
                <br>Public IP: {Fpublicip}</br>
                <br>Time Start: {Ftimestart}</br>
                <br>Time End: {Ftimeend}</br>
                <br></br>
                <br>Approve:</br>
                <a href = {approve} target= "_blank"> Link to approve the deploy</a>
                <br></br>
                <br>Reject:</br>
                <a href = {reject} target= "_blank"> Link to reject the deploy</a>
                <br></br><br></br>
                <form id= "submit_comment" action = "https://0821hdmqr1.execute-api.us-east-1.amazonaws.com/v1/redirect" method = "post" >
                    <label> Send an explanation to {email} writing it in the box below and pressing reject</label><br></br>
                    <textarea id="comment" name= "comment" rows= "5" cols= "100" > </textarea>
                    <input id = "reject_with_comments" name = "reject_with_comments" type = "hidden" value= {reject_with_comments}></input>
                    <input id= "Ftoken" name ="Ftoken" type="hidden" value={Ftoken}></input>
                    <br></br>
                    <input type="submit" value="Reject"></input>
                </form>
                <br></br>
                <br>This email was automatically sent by:</br>
                <br><footer>Denodo Automated Provisioning System (DAPS)</footer></p></br>
            </body>
        </html>
        """.format(
            email=event['name_in_input'],
            name=event['name_in_input'].split("@")[0],
            approve=urls['approve'],
            reject=urls['reject'],
            reject_with_comments=urls['reject_with_comments'],
            Fservice=event['Fservice'],
            Fpublicip=event['Fpublicip'],
            Ftoken =event['Ftoken'],
            Ftimestart=event['Ftimestart'],
            Ftimeend=event['Ftimeend'],
            Frequest=event['Frequest'],
            Fopportunity=event['Fopportunity'],
            executionId= executionId
        )
        #print('Sending email:', email_body)
        #boto3.client('sns').publish(
           #TopicArn=sendArn,
          #  Subject=email_subject,
           # Message=email_body
        #)
       # print('done')
        #return {}
    
    elif event['step'] == 'Send Task Result':
        
        # Compose email
        email_subject = '[DAPS] Your Denodo Automated Provisioning System Request' + ' [Id: ' + executionId + ']'

        if 'Error' in event['output']:
            #selecting message for rejection with/without comments
            if event['output']['Error'] == 'rejected':
                message = ""
            else:
                 message = 'Administrator comment: ' + event['output']['Cause']
                 
            email_body = """Hello,
            
            Your task was rejected! 
            {message}
            Please email this to your manager to follow up if you want a claim.
            
            This email was automatically sent by:
            Denodo Automated Provisioning System (DAPS)
            """.format(
                message = message
            )
            email_body1 = """
                <html>
                    <head> Hello, </head>
                    <body>
                         Your task was rejected!<br> 
                         <p>{message}</p> 
                         <p>Please email this to your manager to follow up if you want a claim.<p>
                        <footer>
                             This email was automatically sent by:<br>
                             Denodo Automated Provisioning System (DAPS)
                        </footer>
                    </body>
                </html>
                """.format(
                    message = message
                    )
        else:
            email_body = """Hello {name},
            
            Your machine has finished .
            
            This email was automatically sent by:
            Denodo Automated Provisioning System (DAPS)
            """.format(
                name=event['output']['name_in_output']
            )
            email_body1 = """
                <html>
                    <head></head>
                    <body>
                        Hello {name},<br> 
                        <br>
                        Your machine has finished<br>
                        <br>
                        <footer>
                             This email was automatically sent by:<br>
                             Denodo Automated Provisioning System (DAPS)
                        </footer>
                    </body>
                </html>
                """.format(
                    name = event['output']['name_in_output']
                    )
    elif event['step'] == 'Send Running Notification':
        
        # Compose email
        email_subject = '[DAPS] Your Denodo Automated Provisioning System Request' + ' [Id: ' + executionId + ']'
        

        email_body = """Hello {name},
        
        Your machine has Started.
        
        Connection Details:
        - Public IP: {instancePublicIp}
        - User: Administrator
        - Password: {instancePassword}
        
        ------NOTE------
        {emailContent}
        ------NOTE------
        
        If you have problems with the connection or your public IP {public_ip} changed, please forward this email to drivas@denodo.com with your problem.
        
        Check your public ip here: whatsmyip.org
        
        This email was automatically sent by:
        Denodo Automated Provisioning System (DAPS)
        """.format(
            name=event['output']['name_in_output'],
            public_ip=event['Fpublicip'],
            instancePassword=event['instancePassword'],
            instancePublicIp=event['instancePublicIp'],
            emailContent=event['emailContent']
            )
        email_body1 = """
            <html>
                 <header></header>
                 <body>
                    Hello {name},<br>
                    Your machine has Started.<br>
                    <br>
                    Connection Details:<br>
                    - Public IP: {instancePublicIp}<br>
                    - User: Administrator<br>
                    - Password: {instancePassword}<br>
                    <br>
                    ------NOTE------<br>
                    {emailContent}<br>
                    ------NOTE------<br>
                    <br>
                    <p> If you have problems with the connection or your public IP {public_ip} changed, please forward this email to drivas@denodo.com with your problem.</p>
                    Check your public ip here: whatsmyip.org<b
                    <footer>
                        This email was automatically sent by:<br>
                        Denodo Automated Provisioning System (DAPS)
                    </footer>
                 </body>
            </html>
            """.format(
            name=event['output']['name_in_output'],
            public_ip=event['Fpublicip'],
            instancePassword=event['instancePassword'],
            instancePublicIp=event['instancePublicIp'],
            emailContent=event['emailContent']
            )
    elif event['step'] == 'Send Approved Confirmation':
        # Compose email
        email_subject = '[DAPS] Your Denodo Automated Provisioning System Request' + ' [Id: ' + executionId + ']'

        if 'Error' in event['output']:
            email_body = """Hello,
            
            Your task was rejected! 
            Please email this to your manager to follow up if you want a claim.
            
            This email was automatically sent by:
            Denodo Automated Provisioning System (DAPS)
            """.format(
                cause=event['output']['Cause']
            )
            email_body1 = """
                <html>
                    <head> Hello, </head>
                    <body>
                         <br>Your task was rejected!</br> 
                         <br>Please email this to your manager to follow up if you want a claim.</br>
                         <br></br>
                        <footer>
                             This email was automatically sent by:<br>
                             Denodo Automated Provisioning System (DAPS)
                        </footer>
                    </body>
                </html>
                """.format(
                    name = event['output']['Case']
                    )
        else:
            email_body = """Hello {name},
            
            Your task was approved and it's scheduled from {startDate} GMT to {endDate} GMT.
            
            If there is any error with the dates please forward this email to drivas@denodo.com with your issue.
            
            This email was automatically sent by:
            Denodo Automated Provisioning System (DAPS)
            """.format(
                name=event['output']['name_in_output'],
                startDate= event['Ftimestart'],
                endDate= event['Ftimeend']
            )
            email_body1 = """
                <html>
                    <header></header>
                    <body>
                        Hello {name},<br>
                        <br>
                        Your task was approved and it's scheduled from {startDate} GMT to {endDate} GMT.<br>
                        <br>
                        If there is any error with the dates please forward this email to drivas@denodo.com with your issue.<br>
                        <br>
                        <footer>
                            This email was automatically sent by:<br>
                            Denodo Automated Provisioning System (DAPS)
                        </footer>
                    </body>
                </html>
            """.format(
                name=event['output']['name_in_output'],
                startDate= event['Ftimestart'],
                endDate= event['Ftimeend']
                )
    else:
        raise ValueError

    print('Sending email:', email_body)
    send_email(event['name_in_input'], email_subject, email_body,email_body1)
    #boto3.client('sns').publish(
    #    TopicArn=sendArn,
    #    Subject=email_subject,
    #    Message=email_body
    #)
    print('done')
    return {}