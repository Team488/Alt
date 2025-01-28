# an order, otherwise known as a command will be triggered and then run once.
# lifespan: 1. create 2. run 3. close
# NOTE: Orders will get processwide "shared" objects passed in via init.
# For things pertaining only to the order, create them in the create method

from abstract.Order import Order

class OrderExample(Order):
    # this example will print information
    def create(self):        
        # here i will get my info
        self.sigma = self.central.map.sigma

    def run(self):
        print(f"Sigma is: {self.sigma}")
    
    def close(self):
        print(f"Cleaning up!")