let AWS = require('aws-sdk');

var responseString = "vacio_definido";

exports.handler = (event, context, callback) => {
    //const response = {
    //    statusCode: 200,
    //    body: JSON.stringify('Successful Denodian Node JS Execution! Great Job!'),
    //};
    //return response;
    
    // set the region
    AWS.config.update({region:'us-east-1'});
    
    // create an ec2 object
    const ec2 = new AWS.EC2({apiVersion: '2016-11-15'});
    responseString = "vacio_definido";
    
    // setup instance params
    const params = {
      InstanceIds: [
        event.instanceId    
      ]
    };
    var descparams = {
      Filters: [
        {
          Name: "resource-id",
          Values: [
            event.instanceId
          ]
        },
        {
          Name: "key",
          Values: [
            "AutomatedEndTime"
          ]
        }
      ]
    }
    var endTimeTag = "0";
    
    if (event.isStopped.isStopped == "Yes"){
      
      console.log(event.isStopped.isStopped);
      console.log("stop");
      
      //Get end time tag assigned to EC2 machine
      
      ec2.describeTags(descparams, function(err, data) {
        if (err) {
          console.log(err, err.stack); // an error occurred
        } else if (data) {
          console.log(data);           // successful response
          
          endTimeTag = data.Tags[0].Value;
          
          console.log(endTimeTag);
      
          //stop machine only if latest end time was set by this request
          if (new Date(endTimeTag) <= new Date(event.Ftimeend)) {
            ec2.stopInstances(params, function(err, data) {
              if (err) {
                console.log(err, err.stack); // an error occurred
              } else if (data) {
                console.log(data);           // successful response
              }  
             
            });
          }
        }  
       
      });
      
      callback(null, responseString);
      
    }else{
      
      console.log(event.isStopped.isStopped);
      console.log("start");
      
      ec2.startInstances(params, function(err, data) {
        if (err) {
          console.log(err, err.stack); // an error occurred
        } else if (data) {
          console.log(data);           // successful response
        }  
      });
      
      //Get end time tag assigned to EC2 machine
      ec2.describeTags(descparams, function(err, data) {
        if (err) {
          console.log(err, err.stack); // an error occurred
        } else if (data) {
          console.log(data);           // successful response
          endTimeTag = data.Tags[0].Value;
          console.log(endTimeTag);
          
          if (new Date(endTimeTag) < new Date(event.Ftimeend)){
            
            var descparams = {
              Resources: [
                event.instanceId
              ],
              Tags: [
                {
                  Key: "AutomatedEndTime",
                  Value: event.Ftimeend
                }
              ]
            }
            
            ec2.createTags(descparams, function(err, data) {
              if (err) {
                console.log(err, err.stack); // an error occurred
              } else if (data) {
                console.log(data);           // successful response
              }
            });
          }
        }
      });
      
      /*
      responseString = "Hello Denodian, " + event.femail + "! This is a successful async response from Node JS! Your test machine i-02bca19a278848cd9 is starting... " + "\n\r";
      responseString = responseString + "Service: " + event.Fservice + "\n\r";
      responseString = responseString + "Public IP: " + event.Fpublicip + "\n\r";
      responseString = responseString + "Time Start: " + event.Ftimestart + "\n\r";
      responseString = responseString + "Time End: " + event.Ftimeend + "\n\r";
      responseString = responseString + "Report Email: " + event.reportemail + "\n\r";
      */
      
      ec2.waitFor("instanceRunning",params, function (err, data) {
        if (err) {
          console.log("errorwait");
          console.log(err);
        }else{
          console.log("successwait");
          ec2.describeInstances(params, function (err, data) {
            if (err) {
              console.log(err);
            }
    
            console.log(data);
            console.log(data.Reservations[0].Instances[0]);
            console.log(data.Reservations[0].Instances[0].PublicIpAddress);
            responseString = data.Reservations[0].Instances[0].PublicIpAddress;
            callback(null, responseString);
          });
        }
      });
      console.log("outwait");
      
    }
    
};

