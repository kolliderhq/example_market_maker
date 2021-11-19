## Kollider Simple Market Maker

**CAOUTION**: Use at your own risk. This repo is meant to be a reference and created for educational purpose only. Do not use in production!

### How To Use

Add your API Keys, Secret and Passphrase to the `config.yaml`. 

Install dependencies
```
pip install -r requirements.txt
```

Run the market maker
```
python src/main.py
```

### Current Strategies

You can configer the stragegy of the Market Maker in the `conig.yaml`. 

1. Mid Price

The mid price strategy will place orders symmetrical and in set intervals around the mid price of the Kollider book. 

2. Index Market Maker

The index price market making strategy will place orders around the index price of underlying asset.
