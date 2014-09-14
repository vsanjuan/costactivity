from persistent import Persistent
import transaction
import ZODB
import ZODB.FileStorage

class Product(Persistent):
	"""Models a product composition by listing the materials and activities
	needed to produce it.
	
	Attributes:
	
	Code: A key that uniquely identifies the product.
	Name: Name of the product.
	Materials: List of materials, and amounts needed to make the product.
	Activities: List of activities and its consumption needed to make the product. 
	"""

	def __init__(self, code, name, description, base_unit):
		"""Creates a new product"""
		self.code = code
		self.name = name
		self.description = description
		self.bill_of_materials = {}
		self.billofactivities = {}
		
	def addMaterial(self, material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 ):
		''' Adds a new material to the product list and the information related 
		to the consumption to the F.P. production the parameters are the following:
		material_code : Code of the material to be consumed.
		consumption: Amount of material consumed.
		consumption_unit: Unit in which the consumption amount is expressed.
		production_ratio: Units of F.P. to which the consumption is referred.
		production_unit : Unit of production to which the production ratio is related.
		waste: % of the material thrown to the waste.
		'''
		self.bill_of_materials[material_code] = {'material_code': material_code,
										'consumption': consumption,
										'consumption_unit' : consumption_unit,
										'production_unit': production_unit,
										'production_ratio': production_ratio,
										'waste' : waste,
										'cost_per_unit': cost_per_unit}
		# self.bill_of_materials._p_changed = True
		self._p_changed = True
		
	def addActivity(self, activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0):
		"""Adds a new activity in the product list needed to make the product and
		the information related with the consumption for each unit on F.P. 
		Parameters:
		consumption: Amount of activity consumed.
		activiy_unit: Unit in which the consumption amount is expressed.
		production_ratio: Units of F.P. to which the consumption is referred.
		production_unit : Unit of production to which the production ratio is related.
		"""
		self.activities[activity_code] = {	'activity_code': activity_code, 
											'consumption': consumption,
											'activity_unit': activity_unit,
											'production_ratio': production_ratio,
											'production_unit': production_unit,
											'cost_per_unit' : cost_per_unit	}
		self.billofactivities._p_changed = True
		self._p_changed = True
		
		
	def CalculateCost(self):
		"""Calculates the direct product cost based on materials and activities consumption.
		This function doesn't check yet:
		A. Consumption units and price units for the activities are homogeneous.
		B. production ratios per unit of output are homogeneous among the activities.
		Parameters:
		Product code
		Returns two values:
			1. Total material cost.
			2. Total activity cost.
		"""
	
		 # Recovers the information about activities and materials needed to calculate the cost
		 # Maybe it would be better to filter the activities and materials in the bill of materials
		 # and bill of activities. I will implement this later if too many materials or activities
		 # are loaded in memory.
		 
		#activitytrax = ActivityTrax().activities
		materialtrax = MaterialTrax().materials
		
		#print materialtrax
		 
		material_cost = 0
		activity_cost = 0
		
		for material_code, material_usage in self.bill_of_materials.items():
			print materialtrax[material_code].name, " " , materialtrax[material_code].cost_per_unit, " " , material_usage["consumption"]
			material_cost += materialtrax[material_code].cost_per_unit * int(material_usage["consumption"])
		
		# for activity_code, activity_usage in self.billofactivities:
			# activity_cost += activitytrax[activity_code].cost_per_unit * activity_usage.consumption
	
		return    material_cost #, activity_cost materialtrax
		
	def __str__(self):
	
		pass
	
	
		
class Activity(Persistent):

	def __init__(self, code, name, description, cost_per_unit, activity_unit):
		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.activity_unit = activity_unit
		
	def cost_per_product(self, product, consumption):
		
		return consumption * self.cost_per_unit
		
	def __str__(self):

		return ("Activity Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.activity_unit))
		
	
		
		
class Material(Persistent):
	
	def __init__(self, code, name, description, cost_per_unit, base_unit):
		self.code = code
		self.name = name
		self.description = description
		self.cost_per_unit = cost_per_unit
		self.base_unit = base_unit
	
	def cost_per_product(self, consumption):
	
		return consumption * self.cost_per_unit
	
	def __str__(self):
	
		return ("Material Code: %s, Name: %s,\n Description: %s,\n Cost per unit: %s\n Base unit: %s"
				% (self.code, self.name, self.description, self.cost_per_unit, self.base_unit))
		
class Trax(object):

	db = ZODB.DB(ZODB.FileStorage.FileStorage("products.fs"))
	connection = db.open()
	root = connection.root()

	def __init__(self, intro = "Product trax product tracking helper",
			 db_path="products.fs"):
				 
		self.intro = intro

		
class ProductTrax(Trax):

	def __init__(self, intro = "Product trax  tracking helper",
			 db_path="products.fs"):

		Trax.__init__(self)
		
		if 'products' in self.root:
			self.products = self.root['products']
		else:
			self.products = self.root['products'] = {}


	def addProduct(self, code, name, description, base_unit):
		
		product = Product( code, name, description, base_unit)
		self.products[code] = product
		transaction.commit()
		
	def addActivity(self, product_code, activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0):
	
		self.products[product_code].addActivity( activity_code, consumption, activity_unit, 
						  production_ratio, production_unit, cost_per_unit = 0)
		
	def addMaterial(self, product_code, material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 ):
						  
		print "From ProductTrax addMaterial product name: exit"				  
		print self.products[product_code].name
	
		self.products[product_code].addMaterial( material_code, consumption, consumption_unit, 
						  production_ratio, production_unit,  waste, cost_per_unit= 0 )
		
	def list_products(self):
		print "Product			Title"
		print "=======          ====="
		for name, product in self.products.items():
			print "%-20s%s" % (name, product.description)
			
	def list_materials(self, productcode):
		print "Product: %s" % productcode
		print
		print " Material"
		print "========="
		for productcode, product in self.products[productcode].materials.items():
			print product.name
			
			
class MaterialTrax(Trax):
		
	def __init__(self, intro = "Material trax  tracking helper",
			 db_path="products.fs"):
				 
		Trax.__init__(self)
		if 'materials' in self.root:
			self.materials = self.root['materials']
		else:
			self.materials = self.root['materials'] = {}
		
		
	def addMaterial(self, code, name, description, cost_per_unit, base_unit):
	
		material = Material( code, name, description, cost_per_unit, base_unit)
		print self.materials.items()
		self.materials[code] = material
		transaction.commit()
		
class ActivityTrax(Trax):
		
	def __init__(self, intro = "Material trax  tracking helper",
			 db_path="products.fs"):
				 
		Trax.__init__(self)
		if 'activities' in self.root:
			self.activities = self.root['activities']
		else:
			self.activities = self.root['activities'] = {}
		
		
	def addActivity(self, code, name, description, cost_per_unit, activity_unit):
	
		activity = Activity( code, name, description, cost_per_unit, activity_unit)
		self.activities[code] = activity
		transaction.commit()
		

			
			
if __name__ == '__main__':
	
	
	materials = MaterialTrax()	
	
	materials.addMaterial(1, "PPC 5mm 1000 gm2", "Polipropileno celular 5 mm 1000 grs / m2",100, "plancha")
	materials.addMaterial(2, "PPC 5mm 1200 gm2", "Polipropileno celular 5 mm 1200 grs / m2",50, "plancha")
	
	
	# print materials.materials[1]
	
	# products = ProductTrax()
	
	# activities = ActivitiyTrax()
	
	# activities.addActivity(1, "Coser", "Coser", 100, "ML")
	# activities.addActivity(2, "Cortar", "Cortar", 50, "Cortes")
	
	# print activities.activities[1]
	# print activities.activities[2]
	
	# products.addProduct(1, "Caja A", "Caja PPC", "caja")
	
	# print products.products[1].name
	
	products = ProductTrax()
	
	print products
	# print products.products[1].__dict__
	# print products.products[1].__methods__
	print products.products[1].code
	print products.products[1].name

	print '*' * 80
	
	#products.addMaterial(1,1, 10,"Kg.", 1, "Unit", 5)
	# products.products[2].addMaterial(1, 10,"Kg.", 1, "Unit", 5)
	
	# print products.products[1].billofmaterials
	
	print '*' * 80
	
	productA = Product(1, "Caja A", "Caja PPC", "caja")
	productB = Product(1, "Caja A", "Caja PPC", "caja")
	
	productB.addMaterial(1, 10,"Kg.", 1, "Unit", 5)
	productB.addMaterial(2, 20,"Kg.", 1, "Unit", 10)
	
	print "Bill of materials \n", productB.bill_of_materials
	
	cost =  productB.CalculateCost()
	# print cost[2].cost_per_unit
	
	print cost
	
	print "*" * 80
	
	# for code, material in cost.items():
	
		# print cost
		# print material
	
	
	
	
		