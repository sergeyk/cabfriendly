from threading import Thread
from Queue import Queue
from random import randint
import time, sys, os, smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText


class Worker(Thread):
	def __init__(self, id, Q):
		Thread.__init__(self)
		self.id = id
		self.Q = Q
		self.live = True
	
	def stop(self):
		self.live = False
	
	def die(self):
		try:
			mailserver.quit()
		except:
			pass
		print 'Thread %d dying.' % self.id
		
		
	def run(self):
		username = 'cabfriendly@gmail.com'
		password = 'flashmapp22'
		try:
			mailserver = smtplib.SMTP('smtp.gmail.com',587)
			mailserver.ehlo()
			mailserver.starttls()
			mailserver.ehlo()
			mailserver.login(username,password)
		except Exception, e:
			print 'Exception:',e
			return self.die()
			
		while self.live:
			recipient, subject, note = self.Q.get().split('$$')
			msg = MIMEMultipart()
			msg['From'] = 'CabFriendly <%s>' % username
			msg['To'] = recipient
			msg['Subject'] = subject
			msg.attach(MIMEText(note))
			try:
				mailserver.sendmail(username, recipient, msg.as_string())
			except Exception, e:
				print 'Exception:',e
				self.Q.put('$$'.join([recipient, subject, note]))
				return self.die()



class Watcher(Thread):
	def __init__(self, Q, monitor_dir):
		Thread.__init__(self)
		self.Q = Q
		self.monitor_dir = monitor_dir
		self.die = False
	
	def stop(self):
		self.die = False
	
	def run(self):
		while not self.die:
			notes = os.listdir(self.monitor_dir)
			for note_id in notes:
				if not note_id[0:4] == 'note':
					continue
				note_path = '%s/%s' % (self.monitor_dir, note_id)
				note = file(note_path, 'r').read()
				self.Q.put(note)
				os.remove(note_path)
		
			time.sleep(1)
			

class PoolManager(Thread):

	def __init__(self, Q, monitor_dir, base_size, q_thresh):
		Thread.__init__(self)
		self.Q = Q
		self.monitor_dir = monitor_dir
		self.q_thresh = q_thresh
		self.pool = []
		self.base_size = base_size
		self.worker_id = 0
		
	def run(self):
		self.add_workers(self.base_size)
		print 'PoolManger: Started with %d workers.' % self.worker_id
		self.monitor()
		
	def add_workers(self, n): 
		for i in xrange(n):
			if self.num_workers() >= 5:
				return
			w = Worker(self.worker_id, self.Q)
			w.start()
			self.pool.append(w)
			self.worker_id += 1
		
		print 'PoolManger: Added %d workers. %d workers total.' % (n, self.num_workers())  
	
	def remove_workers(self, n):
		for i in xrange(n):
			if len(self.pool) <= base_size:
				break
			if self.pool[0].is_alive():
				self.pool[0].stop()
				self.pool[0].join()
			del self.pool[0]
		
		print 'PoolManger: Removed %d workers. %d workers remain.' % (n, self.num_workers())  
	
	def num_workers(self):
		return len(self.pool)
	
	def monitor(self):
		full_iters = 0
		empty_iters = 0
		while True:
			if self.Q.qsize() > self.q_thresh:
				print "Full iters:",full_iters, "Queue Size:", self.Q.qsize()
				if full_iters == 10:
					self.add_workers(1)
					full_iters = 0
				else:
					full_iters += 1
			else:
				full_iters = 0
			
			if self.Q.empty():
				if empty_iters == 10 and len(self.pool)>1:
					self.remove_workers(1)
					empty_iters = 0
				else:
					empty_iters += 1
			else:
				empty_iters = 0
		
			time.sleep(0.1)
			
			r = randint(0, self.num_workers()-1)
			if not self.pool[r].is_alive():
				print 'Randomly detected that thread %d is dead. Restarting.' % r
				del self.pool[r]
				self.add_workers(1)

class NotificationHandler:
	
	def __init__(self, monitor_dir, init_p_size, q_thresh):
		self.Q = Queue()
		self.watcher_args = (self.Q, monitor_dir)
		self.pm_args = (self.Q, monitor_dir, init_p_size, q_thresh)
		self.watcher =  Watcher(*self.watcher_args)
		self.pool_manager = PoolManager(*self.pm_args)
		
		self.watcher.start()
		self.pool_manager.start()
		self.monitor()
		
	def monitor(self):
		while True:
			if not self.watcher.is_alive():
				self.watcher = Watcher(*self.watcher_args)
				self.watcher.start()
				
			if not self.pool_manager.is_alive():
				self.pool_manager = PoolManager(*self.pm_args)
				self.pool_manager.start()
				
			time.sleep(10)
		
if len(sys.argv) != 4:
	print 'Usage: python notifications_server.py <monitor_dir> <init_pool_size> <queue_grow_thresh>'
else:
	print time.strftime("%a, %d %b %Y %H:%M:%S")+': NotificationHandler started.'
	n = NotificationHandler(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
	print time.strftime("%a, %d %b %Y %H:%M:%S")+': NotificationHandler died.'

	