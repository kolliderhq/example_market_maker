## Kollider Simple Market Maker

**CAUTION**: Use at your own risk. This repo is meant to be a reference and created for educational purposes only. Do not use in production!

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

You can configure the strategy of the Market Maker in the `config.yaml`. We are following the framework laid out in ["Demystifying Market Making"](https://kollider.medium.com/long-story-short-demystifying-market-making-98efe4f709da).

#### Mid Price

The mid price strategy will place orders symmetrically and in set intervals ("offsets") around the mid price of the Kollider orderbook.

#### Index Market Maker

The index price market making strategy will place orders around the index price of underlying asset.
