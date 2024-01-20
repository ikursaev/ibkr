How many stocks should I buy to create/rebalance Ben Felix's Five Factor portfolio?
=========

https://www.pwlcapital.com/resources/five-factor-investing-with-etfs/

https://www.youtube.com/watch?v=jKWbW7Wgm0w

```
"XIC": 30%
"VUN": 30%
"AVUV": 10%
"XEF": 16%
"AVDV": 6%
"XEC": 8%
```

US counterparts:
```
"VUN": "VTI",
"XEF": "IEFA",
"XEC": "IEMG"
```

1. You need to buy at least one of each stock
2. Run command
```
podman run --name ibeam --env IBEAM_ACCOUNT=your_account --env IBEAM_PASSWORD=your_password -p 5000:5000 voyz/ibeam
```
3. Go to https://localhost:5000 and login
4. Optionally change PREFER_COUNTERPARTS in the script and run `python __init__.py`