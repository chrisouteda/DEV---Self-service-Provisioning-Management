let AWS = require('aws-sdk');

var responseString = "vacio_definido";

exports.handler = (event, context, callback) => {
    
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
    
    if (event.isStopped.isStopped == "Yes"){
      
      console.log(event.isStopped.isStopped);
      console.log("stop");
      
      ec2.stopInstances(params, function(err, data) {
      if (err) {
        console.log(err, err.stack); // an error occurred
      } else if (data) {
        console.log(data);           // successful response
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

