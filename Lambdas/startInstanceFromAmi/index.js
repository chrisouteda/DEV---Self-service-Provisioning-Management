let AWS = require('aws-sdk');

var responseString = "vacio_definido";

exports.handler = (event, context, callback) => {
    
  // set the region
  AWS.config.update({region:'us-east-1'});
    
  // create an ec2 object
  const ec2 = new AWS.EC2({apiVersion: '2016-11-15'});
  responseString = "vacio_definido";
  
  // set termination date
  const terminationdate = new Date (event.Ftimeend);
  terminationdate.setDate( terminationdate.getDate() + parseInt(event.daystowait,10));
  // termination in minutes for testing
  // terminationdate.setMinutes( terminationdate.getMinutes() + parseInt(event.daystowait,10));
  console.log(terminationdate);
  
  //set stopping date
  const stoppingdate = new Date (event.Ftimeend);
      
  // setup params for creating an instance
  const params = {
    MaxCount: "1",
    MinCount: "1",
    LaunchTemplate: {
      LaunchTemplateId: event.launchTemplate,
      Version: '2'
    }
  };
      
  console.log("start");

  ec2.runInstances(params, function(err, data) {
    if (err) {
      console.log(err, err.stack); // an error occurred
    } else if (data) {
      console.log(data);           // successful response
      // parameters for the wait function
      const params_instance = {
        InstanceIds: [
          data.Instances[0].InstanceId
        ]
      };
      // tags to add to the instance
      const params_instance_tags = {
        Resources: [
          data.Instances[0].InstanceId
        ],
        Tags: [
          {
            Key: "AutomatedEndTime", 
            Value: stoppingdate.toISOString()
          },
          {
            Key: "AutomatedTerminationTime",
            Value: terminationdate.toISOString()
          },
          {
            Key: "Owner",
            Value: event.name_in_input
          },
           {
            Key: "Name",
            Value: event.Fservice
          }
        ]
      };
      //tags to add to the image
      const params_template_tags = {
        Resources: [
          event.launchTemplate
        ],
        Tags: [
          {
            Key: event.name_in_input,
            Value: event.name_in_input
          }
        ]
      };
      ec2.createTags(params_template_tags, function(err, data) {
        if (err) {
           console.log(err, err.stack); // an error occurred
        }else{ 
          console.log(data); // successful response
        }
       });
      ec2.createTags(params_instance_tags, function(err, data) {
        if (err) {
           console.log(err, err.stack); // an error occurred
        }else{ 
          console.log(data); // successful response
        }
       });
      ec2.waitFor("instanceRunning",params_instance, function (err, data) {
        if (err) {
          console.log("errorwait");
          console.log(err);
        }else{
          console.log("successwait");
          ec2.describeInstances(params_instance, function (err, data) {
            if (err) {
              console.log(err);
            }else{
              console.log(data);
              console.log(data.Reservations[0].Instances[0]);
              console.log(data.Reservations[0].Instances[0].PublicIpAddress); //obtain public IP
              responseString = {PublicIP: data.Reservations[0].Instances[0].PublicIpAddress, instanceId: params_instance.InstanceIds[0], TerminationTime: terminationdate};
              // send public IP and instanceId to step function
              callback(null, responseString);
            }
          });
        }
      });
      console.log("outwait");
    }  
  });
    
};