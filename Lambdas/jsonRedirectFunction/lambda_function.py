import json,urllib.parse,urllib3

HTML_TEMPLATE = """<html>
<head>
<title>{message}</title>
<body>
{message}<br>
Details:
<pre>
{json}
</pre>
</body>
</html>
"""
def validate_token(token):
    return token == "ast-8+A683=NUIoenmSE¡?DG65bpQW3Ki54vrP93;_"
    
def format_dic(dic):
    for key in dic:
        dic[key] = dic[key][0]
    return dic

def lambda_handler(event, context):
    
    data = event['body']
    #parse urlencoded body into a dictionary
    payload_dic = urllib.parse.parse_qs(data)
    
    #Validating token
    if not validate_token(payload_dic['Ftoken'][0]):
      print("Invalid token in message: " + str(payload_dic['Ftoken'][0]))
      return{"statusCode": 401, "body": "Unauthorized!"}
    
    print('Event_dic: ' + str(payload_dic))
    
    #obtaining url for the post
    url = payload_dic['reject_with_comments'][0]
    print('url: ' + url)
   
    #Deleting url from the dictionary
    payload_dic.pop('reject_with_comments')
   
    #Parsing the dictionary into json format
    payload = format_dic(payload_dic)
    print('Event: ' + str(payload))
    headers = {
        "content-type": "application/json"
    }
    
    http = urllib3.PoolManager()
    response =  http.request('POST', url, headers=headers,body=json.dumps(payload))
    
    print("response status:" + str(response.status))
    if response.status == 200:
        message = "Response accepted!"
    else:
        message = "Response rejected!"
    html_body = HTML_TEMPLATE.format(
        message = message,
        json= response.data.decode('utf-8').replace(",", ",\n").replace("{", "{\n").replace("}", "\n}")
    )
        
    return{"statusCode": response.status, "headers": {"Content-Type": "text/html"},"body": html_body}