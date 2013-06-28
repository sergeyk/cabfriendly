
/**
 * Module dependencies.
 */

var express = require('express')

var app = module.exports = express.createServer();

// Configuration

app.configure(function(){
  app.set('views', __dirname + '/views');
  app.set('view engine', 'jade');
  app.use(express.bodyParser());
  app.use(express.methodOverride());
  app.use(app.router);
  app.use(express.static(__dirname + '/public'));
});

app.set('view options', {
  layout: false
});

app.configure('development', function(){
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true })); 
});

app.configure('production', function(){
  app.use(express.errorHandler()); 
});

// Redis stuff

var redis_port = 6379
//redis_host = '127.0.0.1'
var redis_host = 'ec2-204-236-138-247.us-west-1.compute.amazonaws.com';
var redis = require("redis"),
    client = redis.createClient(redis_port,redis_host);
client.on("error", function (err) {
    console.log("Error " + err);
});

// Routes

app.get('/:ride_id/:user_name/', function(req, res){
  ride_id = "'"+req.params.ride_id+"'";
  user_name = "'"+req.params.user_name+"'";
  res.render('room', {
    title: 'CabFriendly chat',
    ride_id: ride_id,
    user_name: user_name})
});

app.listen(3000);

// Crypto stuff goes here
// TODO


// Bring in the insane power of Now.js
var nowjs = require('now');
var everyone = nowjs.initialize(app);

console.log("Express server listening on port %d in %s mode", app.address().port, app.settings.env);

// chat stuff
nowjs.on('connect', function(){
  // TODO: check for same user joining ride!
  var group = nowjs.getGroup(this.now.ride_id);
  group.addUser(this.user.clientId);
  console.log("User " + this.now.user_name + " joined chat for ride " + this.now.ride_id);
  // fetch cached messages and display them
  var user = this.now;
  client.lrange(this.now.ride_id, 0, -1, function(err, messages) {
    console.log(messages);
    user.cachedMessages(messages);
  });
});

nowjs.on('disconnect', function(){
  console.log("User " + this.now.user_name + " left chat for ride " + this.now.ride_id);
});

everyone.now.distributeMessage = function(message){
  client.rpush(this.now.ride_id, this.now.user_name +': ' + message);
  nowjs.getGroup(this.now.ride_id).now.receiveMessage(this.now.user_name, message);
};

