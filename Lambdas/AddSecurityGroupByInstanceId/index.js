let AWS = require('aws-sdk');

var responseString = "vacio_definido";

exports.handler = (event, context, callback) => {
    
    // set the region
    AWS.config.update({region:'us-east-1'});
    
    // create an ec2 object
    const ec2 = new AWS.EC2({apiVersion: '2016-11-15'});
    responseString = "vacio_definido";
    
    // setup instance params
    var params = {
      InstanceIds: [
        event.instanceId
      ]
    };
    console.log("start calls");
    
    if (event.isStopped.isStopped == "Yes"){
      //Get Security Groups from Machine ID
      ec2.describeInstances(params, function (err, data) {
        if (err) {
          console.log("errorDesc");
          console.log(err);
        }else{
          console.log("successDesc");
          console.log("describeInstance result: " + JSON.stringify(data));
          console.log("describeInstance2 result: " + JSON.stringify(data.Reservations[0].Instances[0].SecurityGroups.map(obj => {
            return obj.GroupId;
          })));
          var securityGroups = data.Reservations[0].Instances[0].SecurityGroups.map(obj => {
            return obj.GroupId;
          });
          console.log("describeInstance3 result: " + JSON.stringify(securityGroups));
          securityGroups = securityGroups.filter((obj) => {return obj !== event.GroupId[0]})
          console.log("Revoking Secgroup: " + JSON.stringify(event.GroupId[0]));
          console.log("describeInstance4 result: " + JSON.stringify(securityGroups));
          params = {
            InstanceId: event.instanceId,
            Groups: securityGroups
          }
          console.log("describeInstance5 result: " + JSON.stringify(params));
          ec2.modifyInstanceAttribute(params, function (err, data) {
            if (err) {
              console.log("modify error: " + err);
            }
            console.log("modify success: " + data);
            callback(null, responseString);
          });
        }
      });
    }else{
      //Get Security Groups from Machine ID
      ec2.describeInstances(params, function (err, data) {
        if (err) {
          console.log("errorDesc");
          console.log(err);
        }else{
          console.log("successDesc");
          console.log("describeInstance result: " + JSON.stringify(data));
          console.log("describeInstance2 result: " + JSON.stringify(data.Reservations[0].Instances[0].SecurityGroups.map(obj => {
            return obj.GroupId;
          })));
          var securityGroups = data.Reservations[0].Instances[0].SecurityGroups.map(obj => {
            return obj.GroupId;
          });
          console.log("describeInstance3 result: " + JSON.stringify(securityGroups));
          securityGroups.push(event.GroupId[0]);
          console.log("Adding Secgroup: " + JSON.stringify(event.GroupId));
          console.log("describeInstance4 result: " + JSON.stringify(securityGroups));
          params = {
            InstanceId: event.instanceId,
            Groups: securityGroups
          }
          console.log("describeInstance5 result: " + JSON.stringify(params));
          ec2.modifyInstanceAttribute(params, function (err, data) {
            if (err) {
              console.log("modify error: " + err);
            }
            console.log("modify success: " + data);
            callback(null, responseString);
          });
        }
      });
    }
    
};

