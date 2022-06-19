import json, os, boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests

def send_email(recipient, subject, body, body_html):
   # This address must be verified with Amazon SES.
   SENDER = "appnotices.saleseng@denodo.com"
 
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
    manager_emails = ["drivas@denodo.com"]
    print('Event:', json.dumps(event))
    print('Context:', str(context))
    # Switch between the two blocks of code to run
    # This is normally in separate functions
    completeExecutionId = event['executionId']
    executionId = completeExecutionId[-36:]
    print(executionId)
    if event['step'] == 'Send Approval Request':

        #translate dates
        Ftimestart_v = event['Ftimestart']
        if Ftimestart_v != '0':
            Ftimestart_v= "ASAP"
        else:
            Ftimestart_v= Ftimestart_v + ' GMT'

        Ftimeend_v = Ftimeend = str(event['Ftimeend']) + ' GMT'
        #old endpoint for SNS --->>     sendArn = os.environ['MANAGER_TOPIC_ARN']
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
        email_subject = '[SSPM] Action Required: Approval Request from ' + event['name_in_input'].split("@")[0] + ' [Id: ' + executionId + ']'

        email_body = """Hello Manager,
Select to Approve or Reject the following request from {email}:
{Frequest}
Opportunity - {Fopportunity}

Details:
Service: {Fservice}
Public IP: {Fpublicip}
Time Start: {Ftimestart}
Time End: {Ftimeend}

Click to approve:
{approve}

Click to reject:
{reject}

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
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
        

        email_body_html= """<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 53.3375px;">&nbsp;</td>
                                <td style="height: 50px; width: 594.662px;" align="left" height="50"><img class="CToWUd"
                                        src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png"
                                        border="0" /> <span
                                        style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL
                                        USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 53.3375px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 594.662px;" align="left" bgcolor="#595F64"><span
                                        style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service
                                        Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;"
                                    colspan="2">
                                    <blockquote>
                                        <p style="color: #555555; text-align: left;">Hello Manager,</p>
                                        <p style="text-align: justify; color: #555;">Select to Approve or Reject the
                                            following request from {email}</p>
                                        <div><strong>Description:</strong> {Frequest}</div>
                                        <div><strong>Opportunity:</strong> {Fopportunity}</div>
                                        <p style="text-align: justify; color: #555;"><strong>Details:</strong></p>
                                        <ul>
                                            <li style="color: #555555; text-align: justify;">Service: {Fservice}</li>
                                            <li style="color: #555555; text-align: justify;">Public IP: {Fpublicip}
                                            </li>
                                            <li style="color: #555555; text-align: justify;">Time Start: {Ftimestart}
                                            </li>
                                            <li style="color: #555555; text-align: justify;">Time End: {Ftimeend}</li>
                                        </ul>
                                        <div class="button-group" style="margin-top: 25px; text-align: center;">
                                            <div class="buttonWrapper" style="margin-bottom: 10px;"><a
                                                    class="button approveButton"
                                                    style="display: block; margin: 0 auto; padding: 10px; text-decoration: none; font-family: Arial, Helvetica, sans-serif; font-size: 16px; color: #1155cc; border: 2px solid #1155cc;"
                                                    href="{approve}" target="_blank">One-click Approve</a></div>
                                            <div class="buttonWrapper"><a class="button rejectButton"
                                                    style="display: block; margin: 0 auto; padding: 10px; text-decoration: none; font-family: Arial, Helvetica, sans-serif; font-size: 16px; color: #d53e26; border: 2px solid #d53e26;"
                                                    href="{reject}" target="_blank">One-click Reject</a></div>
                                        </div>
                                        <p>&nbsp;</p>
                                        <form id="submit_comment" action="{endpoint}/redirect" method="post"><textarea placeholder="Send an explanation writing it in this box and clicking on the button below"
                                                id="comment" cols="80" name="comment" rows="5"> </textarea> <input
                                                id="reject_with_comments" name="reject_with_comments" type="hidden"
                                                value="{reject_with_comments}" /> <input id="Ftoken" name="Ftoken"
                                                type="hidden" value="{Ftoken}" /> <br /><input
                                                style="display: block; margin: 0 auto; padding: 10px; text-decoration: none; font-family: Arial, Helvetica, sans-serif; font-size: 16px; color: white; background-color: #88be00; border: 2px solid #88be00;"
                                                type="submit" value="Reject &amp; Comment" /></form>
                                        <p>&nbsp;</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was
                                            automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;"
                                    colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span
                                                style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp;
                                                &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp;
                                                &nbsp;&nbsp;</span></strong></p>
                                    <blockquote>
                                        <li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong>
                                            If you want to request an extension period while your machine is still
                                            running and before it turns off automatically, <br />please use again the
                                            Google Form and request the resource with "StartDate": &lt;specify a past
                                            date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must
                                            also add in the Description of the request the key words "TIME EXTENSION
                                            REQUEST" apart from the same data that you covered in your previous request.
                                        </li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP
                                                CHANGED</strong> (Check your public ip here: whatsmyip.org): If your
                                            Public IP changed please use again the Google Form and request the resource
                                            again.<br />You must also add in the Description of the request the key
                                            words "PUBLIC IP CHANGE" apart from the same data that you covered in your
                                            previous request.</li>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;"
                                    colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank"
                                            data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a>
                                    </p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents
                                        and any attached files are strictly confidential. <br />If you have received it
                                        in error, please remove this mail and contact <a
                                            href="mailto:postmaster@denodo.com"
                                            target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
            email=event['name_in_input'],
            name=event['name_in_input'].split("@")[0],
            approve=urls['approve'],
            reject=urls['reject'],
            reject_with_comments=urls['reject_with_comments'],
            Fservice=event['Fservice'],
            Fpublicip=event['Fpublicip'],
            Ftoken =event['Ftoken'],
            Ftimestart=Ftimestart_v,
            endpoint= os.environ['REDIRECT_ENDPOINT'],
            Ftimeend=Ftimeend_v,
            Frequest=event['Frequest'],
            Fopportunity=event['Fopportunity'],
            executionId= executionId
        )
        
        #Send email to all managers
        for email in manager_emails :
            send_email(email, email_subject, email_body, email_body_html)
        
        #### OLD SNS Sending method
        #print('Sending email:', email_body)
        #boto3.client('sns').publish(
        #    TopicArn=sendArn,
        #    Subject=email_subject,
        #    Message=email_body
        #)

        print('done')
        return {}
    
    elif event['step'] == 'Send Task Result':
        
        # Compose email
        email_subject = '[SSPM] Notification: Your Self-Service System Request' + ' [Id: ' + executionId + ']'

        if 'Error' in event['output']:
            #selecting message for rejection with/without comments
            if event['output']['Error'] == 'rejected':
                message = ""
            else:
                message = """<p style="color: #555;"><strong>Manager comment:</strong> """ + event['output']['Cause'] + """</p>"""

            print(message)

            email_body_html="""<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 53.3375px;">&nbsp;</td>
                                <td style="height: 50px; width: 594.662px;" align="left" height="50"><img class="CToWUd" src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png" border="0" /> <span style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 53.3375px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 594.662px;" align="left" bgcolor="#595F64"><span style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;" colspan="2">
                                    <blockquote>
                                        <p style="color: #555;">Hello,</p>
                                        <p style="text-align: justify; color: #555;">Your task was rejected! <br />{message}Please email this to your manager to follow up if you want a claim.</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;" colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</span></strong></p>
                                    <ul style="padding-left: 00px;">
                                        <blockquote><li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong> If you want to request an extension period while your machine is still running and before it turns off automatically, <br />please use again the Google Form and request the resource with "StartDate": &lt;specify a past date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.</li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP CHANGED</strong> (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.<br />You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.</li></blockquote>
                                    </ul>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;" colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank" data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a></p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents and any attached files are strictly confidential. <br />If you have received it in error, please remove this mail and contact <a href="mailto:postmaster@denodo.com" target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
                message = message
                #<p style="color: #555;">Hello,</p>
            )
            email_body = """Hello,
            
Your task was rejected! 
{message}
Please email this to your manager to follow up if you want a claim.

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
            """.format(
                message = message
            )
        else:
            email_body_html="""<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 50.35px;">&nbsp;</td>
                                <td style="height: 50px; width: 597.65px;" align="left" height="50"><img class="CToWUd" src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png" border="0" /> <span style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 50.35px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 597.65px;" align="left" bgcolor="#595F64"><span style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;" colspan="2">
                                    <blockquote>
                                        <p style="color: #555;">Hello {name},</p>
                                        <p style="text-align: justify; color: #555;">Your machine has finished!</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;" colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</span></strong></p>
                                    <ul style="padding-left: 00px;">
                                        <blockquote><li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong> If you want to request an extension period while your machine is still running and before it turns off automatically, <br />please use again the Google Form and request the resource with "StartDate": &lt;specify a past date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.</li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP CHANGED</strong> (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.<br />You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.</li></blockquote>
                                    </ul>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;" colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank" data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a></p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents and any attached files are strictly confidential. <br />If you have received it in error, please remove this mail and contact <a href="mailto:postmaster@denodo.com" target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
                name=event['output']['name_in_output']
            )
            email_body = """Hello {name},
            
Your machine has finished .

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
            """.format(
                name=event['output']['name_in_output']
            )
    elif event['step'] == 'Send Running Notification':
        
        # Compose email
        email_subject = '[SSPM] Notification: Your Self-Service System Request' + ' [Id: ' + executionId + ']'
        
        email_body_html="""<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 50.35px;">&nbsp;</td>
                                <td style="height: 50px; width: 597.65px;" align="left" height="50"><img class="CToWUd" src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png" border="0" /> <span style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 50.35px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 597.65px;" align="left" bgcolor="#595F64"><span style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;" colspan="2">
                                    <blockquote>
                                        <p style="color: #555;">Hello {name},</p>
                                        <p style="text-align: justify; color: #555;">Your machine has Started.</p>
                                        <p style="text-align: justify; color: #555;">Connection Details:</p>
                                        <ul>
                                            <li style="color: #555555; text-align: justify;">Public IP: {instancePublicIp}</li>
                                            <li style="color: #555555; text-align: justify;">User: Administrator</li>
                                            <li style="color: #555555; text-align: justify;">Password: {instancePassword}</li>
                                        </ul>
                                        <p style="text-align: justify; color: #555;">{emailContent}</p>
                                        <p style="text-align: justify; color: #555;">If you have problems with the connection, machine or any doubt, please forward this email to <a href="mailto:drivas@denodo.com" target="_blank">drivas@denodo.com</a> with your problem or question.</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;" colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</span></strong></p>
                                    <ul style="padding-left: 00px;">
                                        <blockquote><li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong> If you want to request an extension period while your machine is still running and before it turns off automatically, <br />please use again the Google Form and request the resource with "StartDate": &lt;specify a past date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.</li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP CHANGED</strong> (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.<br />You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.</li></blockquote>
                                    </ul>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;" colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank" data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a></p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents and any attached files are strictly confidential. <br />If you have received it in error, please remove this mail and contact <a href="mailto:postmaster@denodo.com" target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
            name=event['output']['name_in_output'],
            public_ip=event['Fpublicip'],
            instancePassword=event['instancePassword'],
            instancePublicIp=event['instancePublicIp'],
            emailContent=event['emailContent']
            )
        email_body = """Hello {name},
        
Your machine has Started.

Connection Details:
- Public IP: {instancePublicIp}
- User: Administrator
- Password: {instancePassword}

------NOTE------
{emailContent}
------NOTE------

-----------FAQ-----------

-TO EXTEND USAGE: If you want to request an extension period while your machine is still running and before it turns off automatically, 
please use again the Google Form and request the resource with "StartDate": <specify a past date> and "EndDate": <specify your extension date>.
You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.

-YOUR PUBLIC IP CHANGED (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.
You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.


If you have problems with the connection, machine or any doubt, please forward this email to drivas@denodo.com with your problem or question.

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
        """.format(
            name=event['output']['name_in_output'],
            public_ip=event['Fpublicip'],
            instancePassword=event['instancePassword'],
            instancePublicIp=event['instancePublicIp'],
            emailContent=event['emailContent']
            )
        
    elif event['step'] == 'Send Approved Confirmation':
        # Compose email
        email_subject = '[SSPM] Notification: Your Self-Service System Request' + ' [Id: ' + executionId + ']'

        if 'Error' in event['output']:
            email_body_html="""<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 53.3375px;">&nbsp;</td>
                                <td style="height: 50px; width: 594.662px;" align="left" height="50"><img class="CToWUd" src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png" border="0" /> <span style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 53.3375px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 594.662px;" align="left" bgcolor="#595F64"><span style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;" colspan="2">
                                    <blockquote>
                                        <p style="color: #555;">Hello,</p>
                                        <p style="text-align: justify; color: #555;">Your task was rejected! <br />Please email this to your manager to follow up if you want a claim.</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;" colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</span></strong></p>
                                    <ul style="padding-left: 00px;">
                                        <blockquote><li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong> If you want to request an extension period while your machine is still running and before it turns off automatically, <br />please use again the Google Form and request the resource with "StartDate": &lt;specify a past date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.</li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP CHANGED</strong> (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.<br />You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.</li></blockquote>
                                    </ul>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;" colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank" data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a></p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents and any attached files are strictly confidential. <br />If you have received it in error, please remove this mail and contact <a href="mailto:postmaster@denodo.com" target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
                cause=event['output']['Cause']
            )
            email_body = """Hello,
            
Your task was rejected! 
Please email this to your manager to follow up if you want a claim.

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
            """.format(
                cause=event['output']['Cause']
            )
        else:

            #translate dates
            Ftimestart_v = str(event['Ftimestart'])
            if Ftimestart_v == '0':
                Ftimestart_v= "ASAP"
            else:
                Ftimestart_v= str(Ftimestart_v) + ' GMT'

            Ftimeend_v = Ftimeend = event['Ftimeend'] + ' GMT'

            email_body_html="""<div style="background: #efefef;">
    <div class="adM">&nbsp;</div>
    <table width="650" cellspacing="0" cellpadding="0" align="center">
        <tbody>
            <tr>
                <td bgcolor="#FFFFFF">
                    <table style="height: 581px;" border="0" width="650" cellspacing="0" cellpadding="0">
                        <tbody>
                            <tr style="height: 50px;" bgcolor="#ffffff">
                                <td style="height: 50px; width: 53.3375px;">&nbsp;</td>
                                <td style="height: 50px; width: 594.662px;" align="left" height="50"><img class="CToWUd" src="https://ci3.googleusercontent.com/proxy/1azDbHBT8gEIVsjZ5gnKv72Xi1oQwBe-xnZ-DLlefuXTyf13oA-Lt8YKiw-f4mdoWghSKFssIiSYQ3ZFHgui7JHdLjK-QYSvt__s=s0-d-e1-ft#https://community.denodo.com/img/mail/denodo_logo_xs.png" border="0" /> <span style="background-color: #3366ff; color: #ffffff;">&nbsp;INTERNAL USE&nbsp;</span></td>
                            </tr>
                            <tr style="height: 20px;">
                                <td style="height: 20px; width: 53.3375px;" bgcolor="#595F64" height="20">&nbsp;</td>
                                <td style="height: 20px; width: 594.662px;" align="left" bgcolor="#595F64"><span style="font-family: Tahoma,Geneva,sans-serif; font-weight: regular; color: #ffffff; font-size: 16px;">Self-service Provisioning Management</span></td>
                            </tr>
                            <tr>
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 14px; padding: 20px; height: 129px; width: 610px;" colspan="2">
                                    <blockquote>
                                        <p style="color: #555;">Hello {name},</p>
                                        <p style="text-align: justify; color: #555;">Your task was approved and it's scheduled from {startDate} to {endDate}.</p>
                                        <p style="text-align: justify; color: #555;">If there is any error with the dates please forward this email to <a href="mailto:drivas@denodo.com">drivas@denodo.com</a> with your issue.</p>
                                        <p style="text-align: justify; font-size: 13px; color: #555;">This email was automatically sent by:<br />Self-service Provisioning Management (SSPM)</p>
                                    </blockquote>
                                </td>
                            </tr>
                            <tr style="height: 250px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 13px; padding: 20px; width: 610px; height: 219px;" colspan="2">
                                    <p style="color: #555555; text-align: center;"><strong><span style="color: #ffffff; background-color: #ff0000; font-size: 16px;">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;FAQ&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;&nbsp;</span></strong></p>
                                    <ul style="padding-left: 00px;">
                                        <blockquote><li style="color: #555555; text-align: justify;"><strong>EXTEND USAGE:</strong> If you want to request an extension period while your machine is still running and before it turns off automatically, <br />please use again the Google Form and request the resource with "StartDate": &lt;specify a past date&gt; and "EndDate": &lt;specify your extension date&gt;.<br />You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.</li>
                                        <li style="color: #555555; text-align: justify;"><strong>YOUR PUBLIC IP CHANGED</strong> (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.<br />You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.</li></blockquote>
                                    </ul>
                                </td>
                            </tr>
                            <tr style="height: 141px;">
                                <td style="font-family: Verdana, Geneva, sans-serif; color: #333333; font-size: 10px; padding: 20px; height: 141px; width: 610px;" colspan="2">
                                    <p>Denodo Technologies</p>
                                    <p><a href="http://www.denodo.com" target="_blank" data-saferedirecturl="https://www.google.com/url?q=http://www.denodo.com&amp;source=gmail&amp;ust=1650628802199000&amp;usg=AOvVaw0zBSdF4ZnLiws1VolS5b3m">www.denodo.com</a></p>
                                    <p>&nbsp;</p>
                                    <p>Legal Notice<br />The message is intended for the addresses only and its contents and any attached files are strictly confidential. <br />If you have received it in error, please remove this mail and contact <a href="mailto:postmaster@denodo.com" target="_blank">postmaster@denodo.com</a> <br />Thank you.</p>
                                </td>
                            </tr>
                            <tr style="height: 22px;">
                                <td style="height: 22px; width: 650px;" colspan="2">
                                    <table border="0" width="650" cellspacing="0" cellpadding="0">
                                        <tbody>
                                            <tr>
                                                <td bgcolor="#ff3333" height="10">&nbsp;</td>
                                                <td bgcolor="#88B54A" height="10">&nbsp;</td>
                                                <td bgcolor="#086FA1" height="10">&nbsp;</td>
                                                <td bgcolor="#FF8900" height="10">&nbsp;</td>
                                                <td bgcolor="#999999" height="10">&nbsp;</td>
                                                <td bgcolor="#962567" height="10">&nbsp;</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </tbody>
    </table>
</div>""".format(
                name=event['output']['name_in_output'],
                startDate= Ftimestart_v,
                endDate= Ftimeend_v
            )
            email_body = """Hello {name},
            
Your task was approved and it's scheduled from {startDate} to {endDate}.

If there is any error with the dates please forward this email to drivas@denodo.com with your issue.

-----------FAQ-----------

-TO EXTEND USAGE: If you want to request an extension period while your machine is still running and before it turns off automatically, 
please use again the Google Form and request the resource with "StartDate": <specify a past date> and "EndDate": <specify your extension date>.
You must also add in the Description of the request the key words "TIME EXTENSION REQUEST" apart from the same data that you covered in your previous request.

-YOUR PUBLIC IP CHANGED (Check your public ip here: whatsmyip.org): If your Public IP changed please use again the Google Form and request the resource again.
You must also add in the Description of the request the key words "PUBLIC IP CHANGE" apart from the same data that you covered in your previous request.

This email was automatically sent by:
Self-service Provisioning Management (SSPM)
            """.format(
                name=event['output']['name_in_output'],
                startDate= Ftimestart_v,
                endDate= Ftimeend_v
            )
    else:
        raise ValueError

    print('Sending email:', email_body)
    print('Sending email html:', email_body_html)
    send_email(event['name_in_input'], email_subject, email_body, email_body_html)
    #boto3.client('sns').publish(
    #    TopicArn=sendArn,
    #    Subject=email_subject,
    #    Message=email_body
    #)
    print('done')
    return {}