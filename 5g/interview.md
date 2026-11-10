# Radio 4G/5G Interview Notes: Fundamentals and Generations

## 1. Radio basics

- **Radio wave:** electromagnetic energy carrying information. It is characterized by **frequency** (Hz) and **wavelength**.
- **Frequency vs coverage:**
  - Low frequency (700-900 MHz) travels far and penetrates buildings well, but offers less capacity.
  - High frequency (3.5 GHz, mmWave) offers high capacity and speed, but has short range and poor penetration.
- **Bandwidth:** the width of spectrum used. More bandwidth means higher throughput.
- **dB / dBm:** dB is a ratio and dBm is absolute power. Signal strength is negative (for example -90 dBm), and closer to 0 is stronger.
- **Path loss:** signal weakening with distance, walls, and obstacles.
- **Interference:** unwanted signals from other cells that reduce quality. This is why frequency and PCI planning matter.
- **Duplex:** **FDD** uses separate frequencies for uplink and downlink. **TDD** uses the same frequency at different times (5G 3.5 GHz is TDD).
- **Cell and site:** a **site** is one location with antennas, and it has several **cells**, typically 3 sectors. A cell is what a phone connects to.
- **Handover:** moving a call or session from one cell to another without dropping it.
- **Antenna:** radiates the signal in a given direction. Key settings are azimuth, tilt, and height. **MIMO** means using several antennas to increase speed.

## 2. Differences between 2G, 3G, 4G, and 5G

| | **2G (GSM)** | **3G (UMTS)** | **4G (LTE)** | **5G (NR)** |
|---|---|---|---|---|
| Main use | Voice, SMS | Voice, mobile internet | Fast mobile broadband | Ultra-fast, IoT, low latency |
| Base station | BTS (BSC controller) | NodeB (RNC controller) | eNodeB | gNodeB |
| Access technique | TDMA/FDMA | WCDMA | OFDMA (DL) / SC-FDMA (UL) | OFDMA, flexible |
| Typical speed | ~0.1 Mbps (EDGE up to ~0.3) | ~2-42 Mbps (HSPA) | ~100 Mbps - 1 Gbps | ~1 - 10 Gbps |
| Latency | ~500 ms | ~100 ms | ~30-50 ms | ~1-10 ms |
| Typical bands (Tunisia/Europe) | 900, 1800 MHz | 2100, 900 MHz | 800, 1800, 2600 MHz | 700, 3500 MHz (mmWave later) |
| Core network | Circuit-switched | Circuit + packet | All-IP (EPC) | 5G Core (service-based) |
| Key technology | Digital voice | Packet data, soft handover | MIMO, carrier aggregation | Massive MIMO, beamforming, network slicing |

### How to remember the evolution

- **2G:** digital voice and SMS.
- **3G:** brought mobile internet.
- **4G:** all-IP, fast streaming and apps.
- **5G:** speed, very low latency, and massive device connectivity.

## 3. What 5G adds (the three use cases)

- **eMBB:** enhanced mobile broadband (very high speed).
- **URLLC:** ultra-reliable low latency (industry, autonomous vehicles, remote surgery).
- **mMTC:** massive machine-type communication (millions of IoT devices).
- Plus **network slicing**, **beamforming**, and **Massive MIMO**.

## 4. Short answers to likely basic questions

- **Why 5G in higher frequencies if they have shorter range?** Higher frequencies have more spectrum available, so more capacity and speed. Operators combine them with low bands for coverage.
- **Why do we need more sites in 5G?** Higher frequencies cover less distance, so more sites are needed.
- **What is the main change from 3G to 4G?** The move from CDMA to OFDMA and an all-IP architecture, giving much higher speed and lower latency.
- **NSA vs SA:** NSA uses the 4G core with 5G radio, and SA uses a full 5G core.
