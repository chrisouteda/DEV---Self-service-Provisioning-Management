var aws = require("aws-sdk");
var ses = new aws.SES({ region: "us-east-1" });
exports.handler = (event, context) => {
  console.log(event);
  var params = {
    Destination: {
      ToAddresses: ["couteda@denodo.com"],
    },
    Message: {
      Body: {
        Html: {Data: 'Hi!<br />' +
                      event.Input.name+ ' wants to deloy a machine <br />' +
                      'Can you please approve:<br />' +
                      'https://twnsh3n8ok.execute-api.eu-west-3.amazonaws.com/test/succeed?taskToken=' + encodeURIComponent(event.TaskToken) + '<br />' +
                      'Or reject:<br />' +
                      'https://twnsh3n8ok.execute-api.eu-west-3.amazonaws.com/test/fail?taskToken=' + encodeURIComponent(event.TaskToken),
              Charset: 'UTF-8'},
        Text: { Data: "Test" },
      },

      Subject: { Data: "Test Email" },
    },
    Source: "couteda@denodo.com",
  };
  return ses.sendEmail(params,function(err,data) {
    if (err) {
        console.log(err, err.stack);
        context.fail('Internal Error: The email could not be sent.');
    } else {
        console.log(data);
        context.succeed('The email was successfully sent.');
    }
  });
};