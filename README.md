# DiamSploit

DiamSploit is an educational Python project for studying the **Diameter**
protocol and its use in 4G/LTE mobile networks. The project implements a small
part of the Diameter stack and allows you to:

- check for a Diameter service on a host or network;
- open a Diameter connection over TCP or SCTP;
- exchange standard `CER/CEA`, `DWR/DWA`, and `DPR/DPA` messages;
- experiment with selected 3GPP S6a messages, including `AIR/AIA` and
  `ULR/ULA`.

> **Important notice — authorized educational use only**
>
> This tool generates traffic to Diameter services and includes scanning and
> mobile-identity request functionality. It must be used **only** in an
> isolated lab, on systems owned by the user, or on systems for which written
> authorization has been obtained. Do not use it against mobile networks,
> operators, companies, or third-party Internet addresses. The user is
> responsible for complying with all applicable laws, contracts, and policies.
> The authors do not authorize offensive activity, unauthorized access, service
> disruption, or the collection of real user data.

## Diameter overview

**Diameter** is an AAA protocol (*Authentication, Authorization and
Accounting*) used for authentication, authorization, and accounting. It is
widely used in the core of 4G/LTE networks and other telecommunications
systems. It normally uses port `3868` and can run over TCP or SCTP.

A Diameter message consists of a header and a series of **AVPs**
(*Attribute-Value Pairs*). Messages are identified by a command code and an
application ID. Requests generally have a corresponding response:

| Pair | Purpose |
| --- | --- |
| `CER/CEA` | Peer capability negotiation |
| `DWR/DWA` | Peer liveness check |
| `DPR/DPA` | Closing the peer connection |
| `AIR/AIA` | S6a authentication-information request/answer |
| `ULR/ULA` | S6a user-location update request/answer |

In LTE, the **S6a** interface typically connects an MME and an HSS. S6a
requests may contain sensitive data such as IMSIs and authentication
information; they must therefore be tested only with fictional data in a
controlled environment.

## Requirements

- Python 3.10 or later;
- an accessible Diameter lab environment;
- the Python dependencies listed in [`requirements.txt`](requirements.txt);
- SCTP support on the operating system when using `--protocol sctp` or
  `PROTOCOL=SCTP`.

SCTP support depends on the operating system and kernel configuration. TCP is
the simplest option for a local lab.

## Installation

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows PowerShell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The code imports modules from the `src` directory, so run the scripts from the
repository root using `python src/...`.

## Diameter scanner

`diamscan.py` sends a `Capabilities-Exchange-Request` to each target and
classifies the connection result. Use it only against authorized addresses.

Scan a single host:

```bash
python src/diamscan.py --host 127.0.0.1 --port 3868 --protocol tcp
```

Scan a lab network:

```bash
python src/diamscan.py --network 192.0.2.0/28 --port 3868 \
  --protocol tcp --timeout 5
```

Main options:

| Option | Default | Description |
| --- | --- | --- |
| `--host` | — | Single IP address |
| `--network` | — | Network in CIDR notation |
| `--port` | `3868` | Diameter port |
| `--timeout` | `5` | Connection timeout in seconds |
| `--protocol` | `sctp` | `tcp` or `sctp` |

`--host` and `--network` are mutually exclusive, and one of them is required.

## Interactive client

### `.env` configuration

Copy the example file and adjust the values for your lab:

```bash
cp .env.example .env
```

Example configuration:

```dotenv
BIND_IP=127.0.0.1
HOST=127.0.0.1
PORT=3868
PROTOCOL=TCP
ORIGIN_HOST=mme01
MCC=001
MNC=01
PRODUCT_NAME=DiamSploit
BUFFER=4096
```

`HOST` is the destination Diameter peer; `BIND_IP` is the local address used
for binding. `MCC` and `MNC` are used to construct the 3GPP realm. Do not put
credentials, secrets, or real user data in `.env`.

Start the client:

```bash
python src/diamsploit.py
```

After the `CER/CEA` exchange, the program displays an interactive prompt. The
available commands are:

| Command | Action |
| --- | --- |
| `dwr` | Send a Device-Watchdog-Request |
| `air` | Send an Authentication-Information-Request; asks for destination host, realm, and a lab IMSI |
| `ulr` | Send an Update-Location-Request; asks for destination realm and a lab IMSI |
| `exit` | Send a Disconnect-Peer-Request and close the connection |

Use `exit` to end a session so that the `DPR/DPA` exchange and orderly socket
shutdown can take place.

## Project structure

```text
.
├── src/
│   ├── diamscan.py                 # CER scanner for authorized hosts/networks
│   ├── diamsploit.py               # Interactive client
│   └── diameter/
│       ├── diameter.py             # Headers, AVPs, requests, and responses
│       ├── common_messages/        # Common Diameter messages
│       ├── S6a_3GPP/               # AIR/ULR and PLMN encoding
│       └── S6c_3GPP/               # S6c model for SMS
├── .env.example                    # Example configuration
├── requirements.txt
└── LICENSE
```

The S6c module contains the `SendRoutingInfoForSMRequest` model, but it is not
currently exposed through the `diamsploit.py` interactive prompt.

## Known limitations

- this is not a complete Diameter stack implementation;
- it is not a replacement for a peer, HSS, MME, or dedicated test environment;
- message and response handling is intended for controlled experiments, not
  production;
- the project does not implement authentication, encryption, or secure
  identity management;
- S6a messages may affect the remote system: use only simulators and fictional
  identities.

## Recommended lab setup

To reduce risk, use two virtual machines or containers on a private network,
an emulated Diameter peer, and fictional MCC/MNC, IMSI, and realm values.
Capture traffic only with the consent of all system owners involved, and
remove sensitive data from logs before sharing them.

## Wireshark and pyHSS lab

A practical way to observe the protocol without contacting a production
network is to run a local HSS emulator and capture the exchange with
Wireshark. [pyHSS](https://github.com/pyhss/pyhss) is an open-source Python
HSS/Diameter server that supports Diameter base messages and several 3GPP
interfaces, including S6a. Its repository contains the current installation
and configuration instructions.

The following workflow is intended for a private, isolated lab:

1. Install and start pyHSS by following its
   [official documentation](https://github.com/pyhss/pyhss#readme). Use only
   fictional subscriber data and bind it to a lab-only interface.
2. Confirm which address and port expose the pyHSS Diameter service. The
   standard Diameter port is `3868`; do not expose the service to the public
   Internet.
3. Start Wireshark on the interface shared by the client and pyHSS. A capture
   filter can limit the recording to Diameter transport traffic:

   ```text
   tcp port 3868 or sctp port 3868
   ```

4. Configure `.env` with the pyHSS lab address, for example
   `HOST=127.0.0.1`, `PORT=3868`, and `PROTOCOL=TCP`, then start
   `diamsploit.py`.
5. In the interactive prompt, begin with `dwr`. After verifying the
   `CER/CEA` and `DWR/DWA` exchanges, use only the pyHSS test subscribers for
   `air` and `ulr`.
6. Stop the capture after using `exit`, then inspect the packets. Useful
   Wireshark display filters include:

   ```text
   diameter
   diameter.cmd.code == 257
   diameter.cmd.code == 280
   diameter.cmd.code == 318
   diameter.cmd.code == 316
   ```

   The command codes correspond to CER, DWR, AIR, and ULR respectively.
   Expand the Diameter header and AVP trees to compare request/answer flags,
   command codes, application IDs, result codes, origin/destination peers, and
   S6a fields.

The repository also includes example Diameter captures in the
[`traffic/`](traffic/) directory. In particular, the ULR examples are
available for both TCP and SCTP, so they can be opened directly in Wireshark
to study the packet structure and compare the two transports without first
starting a live lab.

This setup makes it possible to observe the complete request/response flow
while keeping all traffic under the experimenter's control. Diameter traffic
in a basic lab is generally visible on the wire, so packet captures must be
treated as sensitive and must not contain real IMSIs or authentication data.

## Contributing

Improvements are welcome and everyone is encouraged to help make this tool
more reliable and useful for education. Contributions may include new
Diameter/3GPP messages, better validation and error handling, Wireshark
examples, tests, documentation, or support for additional lab environments.
Before opening a pull request:

- keep changes focused and explain the educational use case;
- test only against local or explicitly authorized systems;
- never include credentials, real subscriber data, packet captures containing
  personal data, or other secrets;
- preserve the authorized-use and safety guidance in this README.

Issues, documentation fixes, and small reproducible examples are valuable
contributions as well.

## License

This project is distributed under the MIT license. See [`LICENSE`](LICENSE).
