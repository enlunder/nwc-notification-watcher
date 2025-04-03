Nostr Wallet Connect ([NIP-47](https://github.com/nostr-protocol/nips/blob/master/47.md)) is an open protocol enabling applications to interact with bitcoin lightning wallets. 

notification-watcher.py is a short example program showing how to parse a NWC connecting string and connect to the specified relay and watch for NIP-47 notification events. 

Before launch you need to set the NWC environment variable to the connection string of your wallet service.

#### Usage:

```
export NWC="nostr+walletconnect://..."
python nwc-notification-watcher.py
```

