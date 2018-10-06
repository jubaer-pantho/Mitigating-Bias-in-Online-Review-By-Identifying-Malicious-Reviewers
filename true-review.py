#author: Md Jubaer Hossain Pantho
#work on mitigating bias on online review

import networkx as nx
import xml.etree.ElementTree as ET
import os
import sys
import itertools

#counting number of reviews in the dataset
num_lines = sum(1 for line in open('foods-200-reviewers.txt'))
no_reviews = num_lines/9
print "no of reviews: "+ str(no_reviews)


#opening data-set file
G = nx.Graph()
f = open("foods-200-reviewers.txt", "r") 

#generating the network
for i in range(no_reviews):
	lineBuffer = f.readline()
	if "product/productId:" in lineBuffer:
		productID = lineBuffer[len("product/productId: "):(len(lineBuffer)-1)]
	else:
		print "data read error in product ID : ", lineBuffer
	lineBuffer = f.readline()
	if "review/userId:" in lineBuffer:
		userID = lineBuffer[len("review/userId: "):(len(lineBuffer)-1)]
	else:
		print "data read error in user ID : ", lineBuffer
	lineBuffer = f.readline()
	lineBuffer = f.readline()
	lineBuffer = f.readline()
	if "review/score:" in lineBuffer:
		score = lineBuffer[len("review/score: "):(len(lineBuffer)-1)]
	else:
		print "data read error in score : ", lineBuffer
	lineBuffer = f.readline()
	if "review/time:" in lineBuffer:
		reviewTime = lineBuffer[len("review/time: "):(len(lineBuffer)-1)]
	else:
		print "data read error in score : ", lineBuffer
	lineBuffer = f.readline()
	if "review/summary:" in lineBuffer:
		summary = lineBuffer[len("review/summary: "):(len(lineBuffer)-1)]
	else:
		print "data read error in summary : ", lineBuffer
	lineBuffer = f.readline()
	lineBuffer = f.readline()
	
	#adding product node
	if not G.has_node(productID):
		G.add_node(productID, nodeType = "product", evaluation = "null")
	
	#adding user node
	if not G.has_node(userID):
		G.add_node(userID, nodeType = "user", evaluation = "trusted")
	
	#adding edge with attributes
	G.add_edge(productID, userID, weight=score, edgeTime = reviewTime, edgeSum = summary)
	
print "number of nodes : "+ str(G.number_of_nodes())
print "number of edges : " + str(G.number_of_edges())
print "\n"

#iterate through user nodes
for node_index in G.nodes(data=False):
	if (G.node[node_index]['nodeType'] == "user" and G.degree(node_index)>19):
		add=0
		#printing the number of reviews submitted by the user
		print "user id : "+ node_index + "   Review submitted : " + str(G.degree(node_index))
		# calculating variance of rating
		for edge_index in G.edges(node_index, data= True):
			add = add + float(edge_index[2]['weight'])
		
		avg = add/G.degree(node_index)		
		print "average = "+ str(avg)
		var=0
		
		for edge_index in G.edges(node_index, data= True):
			var = var + (float(edge_index[2]['weight']) - avg)*(float(edge_index[2]['weight']) - avg)
		
		#tag non-trusted reviewer with low variance. In this implementation the threshold used is 0.1 
		var= var/G.degree(node_index)
		if var < 0.1:
			G.node[node_index]['evaluation'] = "non-trusted"			
		print "variance = " + str(var)
		
		
		# checking timestamp data. In unix time 48 hours is approximately 220000
		timeFlag=0
		timeCounter=0
		for edge_index in G.edges(node_index, data= True):
			if timeFlag==0:
				prev = float(edge_index[2]['edgeTime']) # storing the previous review time
				timeFlag=1
			else:
				timeDiff = abs(prev- float(edge_index[2]['edgeTime'])) #calculating the time difference between two reviews
				if timeDiff < 220000:
					timeCounter = timeCounter+1
				prev = float(edge_index[2]['edgeTime'])
		
		# if we found 15 cases where a particular reviewer submitted multiple reviews we tag him as non-trusted  
		if timeCounter > 15.0:
			G.node[node_index]['evaluation'] = "non-trusted"
			
		print "multiple review within 48 hours : " + str(timeCounter)
		
		#checking review summary text match. This is a plain text match
		summaryFlag=0
		similarityCount=0
		for edge_index in G.edges(node_index, data= True):
			if summaryFlag ==0:
				prevSum = edge_index[2]['edgeSum']	# storing the previous review summary
				summaryFlag =1;
			else:
				if prevSum == edge_index[2]['edgeSum']: #comparing the results between two consecutive review summary
					similarityCount= similarityCount+1
				prevSum = edge_index[2]['edgeSum']
		
		#tagging the reviewer non-trusted if 33% of the reviews shows pair match	
		print "similarityCount : " + str(similarityCount)
		if (similarityCount > (G.degree(node_index)*0.33)):
			G.node[node_index]['evaluation'] = "non-trusted"
				
		print "trust Status : " + G.node[node_index]['evaluation']+ "\n"
		


#print updated product review
#iterating through each product node within the network
for node_index in G.nodes(data=False):
	if G.node[node_index]['nodeType'] == "product":
		normalRating=0.0
		modRating=0.0
		trustedUserCount=0
		for edge_index in G.edges(node_index, data= True):
			normalRating = normalRating + float(edge_index[2]['weight']) #calculating normal rating
			if G.node[edge_index[1]]['evaluation'] == "trusted":
				modRating = modRating + float(edge_index[2]['weight']) #calculateing modified rating
				trustedUserCount = trustedUserCount+1
		
		normalRating = normalRating/G.degree(node_index)
		#handling divide by 0
		if trustedUserCount==0:
			modRating = 0
		else:
			modRating = modRating/trustedUserCount
			
		
		#printing modified product ratings

		G.node[node_index]['evaluation'] = str(modRating)		
		if normalRating != modRating and modRating!=0:
			print  "product id : " + node_index + " : " +  str(normalRating) + " / " + str(modRating)		
		G.node[node_index]['evaluation'] = str(modRating)	

