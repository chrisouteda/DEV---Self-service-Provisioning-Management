let AWS = require('aws-sdk');

var responseString = "vacio_definido";

exports.handler = (event, context, callback) => {
    
  // set the region
  AWS.config.update({region:'us-east-1'});
    
  // create an ec2 object
  const ec2 = new AWS.EC2({apiVersion: '2016-11-15'});
  responseString = "vacio_definido";
  
  //termination date
  var terminationDate = new Date(event.Ftimeend);
  terminationDate.setDate( terminationDate.getDate() + parseInt(event.daystowait,10));
  // termination in minutes for testing
  //terminationDate.setMinutes( terminationDate.getMinutes() + parseInt(event.daystowait,10));
    
  // setup params for terminating an instance
  var params = {
    InstanceIds: [
      event.instanceId
    ]
  }; 
  const descparams = {
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
          "AutomatedTerminationTime"
        ]
      }
    ]
  };
  console.log(event);
  //setup params for deleting launch template tags 
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
      
  ec2.describeTags(descparams,function(err,data){ 
    if (err) {
      console.log(err, err.stack); // an error occurred
    }else{
      console.log(data);           // successful response
      const terminationDateTag = data.Tags[0].Value;
      console.log(terminationDateTag);
      //terminate if the termination tag is not greater than the termination date of the execution
      if (new Date(terminationDateTag) <= terminationDate){
        console.log("terminate");
        ec2.terminateInstances(params, function(err, data) {
          if (err) {
            console.log(err, err.stack); // an error occurred
          } else if (data) {
            console.log(data);           // successful response
            //delete lt tags
            console.log(params_template_tags);
      
            //delete tags from launch template
            ec2.deleteTags(params_template_tags, function(err, data) {
              if (err){ console.log("error en el delete tags"); console.log(err, err.stack); } // an error occurred
              else console.log(data);           // successful response
            });
            //wait for instance terminated
      
            ec2.waitFor("instanceTerminated",params, function (err, data) {
              if (err) {
                console.log("errorwait");
                console.log(err);
              }else{
                console.log("successwait");
                callback(null, responseString);  
              }  
            }); 
          }  
       
        });
      }
      }
    });
  
  console.log("outwait");
       
};