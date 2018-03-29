import json
import simplekml
import time
import sys
from os import listdir
from os.path import isfile, join, isdir
import csv


def cleanJson(database):
	content = database.readlines()
	if "\x00" in (content[-1]):  #Busco byte asociado a informacion NULA, Chequeo solo la ultima linea
		content = content[:-1]
		print("Limpie el archivo")
	return content

def convert_coordinates(string):  #Transforma coordenadas con Orientacion al final a numero, probado con Formato 2- Limpio 2.json
	if isinstance(string, float):
		output = string
	else:
		output = string
		if string[-1].isalpha():
			if string[-1] in ["S","W"]:
				output = -float(string[:-1])/100
			else:
				output = float(string[:-1])/100

	return output

def remove_duplicates(x):  #Elimina duplicados de informacion (duplicados perfectos)
	return list(set(x))


class JsonData():
	def __init__(self):
		self.master_database= [] #lista de diccionarios

	@property
	def gps_database(self):
		output=[]
		for i in self.master_database:
			if "sensors" in i.keys():
				for sensor in i["sensors"]:
					if sensor["sensorType"] == "GPS6000":
						dic = sensor["data"]  #Aparentemente no siempre es el primero!
			else:
				dic = i["data"]  #Su longitud y latitud tienen una letra al final:

			if dic["_RAW"] != "" and dic["valid"] in ["1","2","3","4","5"]:
				dic["timestamp"]=i["timestamp"]
				output.append(dic)
		return output

	def export_to_kml(self,output_path):
		data_invalida = [] #Solo util para debug
		lineas_invalidas = 0
		data_locaciones = []
		for dic in self.gps_database:
			try:
				lon = convert_coordinates(dic["longitude"])
				lat = convert_coordinates(dic["latitude"])
				datatime = int(float(dic["timestamp"]))
				data_locaciones.append((lat,lon,datatime))
			except:
				lineas_invalidas+=1
				data_invalida.append(dic)

		#print(data_locaciones)
		print("Numero de lineas no parseadas: {}".format(lineas_invalidas))
		#for i in data_invalida:
		#	print(i)
		kml = simplekml.Kml()
		for i in data_locaciones:
			pnt = kml.newpoint(name= time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i[2])), coords=[(i[0],i[1])])  # lon, lat, optional height
			pnt.timestamp.when = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.localtime(i[2]))
		kml.save(output_path+"/"+"output.kml")

		print("Exporte archivo KML")


	def add_data(self,ruta):  #Agregar el filtro de limpieza de data aca
		if ruta[-5:] == ".json":
			with open(ruta, 'r') as content:
				database = cleanJson(content) #Lista de diccionarios, cada diccionario es un log
				self.master_database += [json.loads(i) for i in database] #Lista de objetos JSON
				print("Importe el archivo {}".format(ruta))
		elif isdir(ruta):
			files = [f for f in listdir(ruta) if isfile(join(ruta, f))]
			contador = 0
			for i in files:
				if i[-5:] == ".json":  #Reconozco aquellos archivos que son .json
					with open(ruta+"/"+i, 'r') as database:
						print("Abri archivo {}".format(ruta+"/"+i))
						content = cleanJson(database) #Lista de diccionarios, cada diccionario es un log
						self.master_database += [json.loads(i) for i in content] #Lista de objetos JSON
						contador+=1
			print("Numero de archivos .json importados: {}".format(contador))
		else:
			print("Error al importar")


	def clean_data(self):  #Export_Kml lo tiene incorporado, pero en caso de solo querer limpiar aca esta la funcion
		contador=0
		eliminados = []
		for i in self.master_database:
			if "sensors" in i.keys(): #Existen 2 formatos distintos 
				dic = i["sensors"][0]["data"]  
			else:
				dic = i["data"]  #Su longitud y latitud tienen una letra al final

			if dic["_RAW"] == "" or dic["valid"] not in ["1","2","3","4","5"]:  #Codigos asociados a data valida
				self.master_database.remove(i)
				contador+=1
				eliminados.append(i)

		#print(eliminados)
		print("Numero de entradas eliminadas: {}".format(contador))


	def export_to_csv(self,output_path,opcion):  #Para que funcione a de modificarse la estructura de datos a solo aquello que nos importa
		if opcion == "gps":
			data = self.gps_database

		keys = data[0].keys()
		with open(output_path, 'w') as output_file:
			dict_writer = csv.DictWriter(output_file, keys)
			dict_writer.writeheader()
			dict_writer.writerows(data)
		print("Exporte la data a csv")


	def review_speed(self):
		output=[]
		for x, y in zip(self.master_database[:-1], self.master_database[1:]):
			pass


if __name__ == '__main__':
	x = JsonData()
	x.add_data("/Users/benjamimo1/Documents/AgroBolt/Data-test/Formato1-Limpio.json")
	x.clean_data()
	#for i in x.gps_database:
	#	print(i)
	x.export_to_csv("/Users/benjamimo1/Documents/AgroBolt/Data-test/output.csv","gps")
	x.export_to_kml("/Users/benjamimo1/Documents/AgroBolt/Data-test")

	
	#toCSV = [{'name':'bob','age':25,'weight':200},
         #{'name':'jim','age':31,'weight':180}]
	#data_to_csv(toCSV,"/Users/benjamimo1/Documents/AgroBolt/Data-test/output.csv")



