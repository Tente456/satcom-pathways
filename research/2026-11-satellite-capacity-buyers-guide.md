---
title: Buying satellite connectivity, a plain-language guide
type: Guide
date: 2026-11-17
author: Satcom Pathways Research
summary: What Mbps, MHz, committed rates, contention, availability and latency mean when you buy satellite capacity or a LEO service plan, and why the cheapest price per MHz is often not the cheapest network.
tags: Procurement, GEO, LEO broadband, Guide
---

Satellite offers are hard to compare because suppliers price them in different units. One quotes dollars per MHz, another a monthly fee per terminal, a third a "10 Mbps service" with no detail behind it. This guide explains the terms that decide what you actually get and what it really costs.

## Start with what the network has to do

Before asking for prices, write down what the network must carry. Suppliers can only quote properly against a clear requirement.

- **Sites.** How many, where they are and whether more will be added later.
- **Traffic per site.** The data rate each site needs at its busiest hour, in both directions.
- **Applications.** Voice and video calls are sensitive to delay. Email and file transfer are not.
- **Availability.** How much downtime each site can live with in a year.
- **Contract length.** Prices and equipment choices change with the term.

## Mbps and MHz are not the same thing

You need data rate, measured in megabits per second (Mbps). Geostationary operators sell bandwidth on a satellite, measured in megahertz (MHz). The link between the two is spectral efficiency, in bits per second per hertz (bps/Hz).

Efficiency depends on the modem, the modulation and coding it uses, the antenna size and the power of the satellite beam. Better equipment squeezes more Mbps out of each MHz.

At 1.6 bps/Hz, carrying 10 Mbps takes 6.25 MHz. At 2.8 bps/Hz the same 10 Mbps takes 3.57 MHz, which is 43% less bandwidth to pay for every month. Always ask a supplier what efficiency its price assumes.

## Committed rate, burst rate and contention

A "1 Mbps service" means little until you know how much of it is guaranteed.

- **Committed information rate (CIR).** The rate you get at all times, even when the network is busy.
- **Maximum or burst rate (MIR).** The rate you can reach when spare capacity is free. It is not guaranteed.
- **Contention ratio.** How many users share the same capacity. At 10 to 1, up to ten users share each unit, so busy hours can be slow.

Two offers with the same headline speed can differ a lot in committed rate and contention. Compare those numbers, not the headline.

## Availability and rain

Availability is the share of the year a link works. Small differences matter. A year has 8,760 hours, so 99.5% availability allows about 44 hours of outage a year, and 99.9% allows under 9 hours.

Heavy rain weakens satellite signals, and higher frequency bands are hit harder. Ka-band is the most affected of the common bands, Ku-band less so and C-band least. Much of Africa sees intense tropical rain, so ask what availability a price is designed for, in which band and for which locations. Extra margin for rain costs more bandwidth or larger antennas, and it should be in the quote, not added later.

## Delay

A geostationary satellite sits about 36,000 km above the equator. A request and its reply travel up and down twice, so each round trip takes around half a second. Low Earth orbit (LEO) satellites are far closer and add much less delay. For voice, video calls and interactive apps this difference can matter more than speed.

## GEO capacity and LEO service plans are priced differently

With geostationary (GEO) capacity you either lease MHz and run your own network of modems and a hub, or buy a managed service from a provider that does this for you. The main costs are bandwidth per month, equipment and teleport or support fees.

LEO broadband is usually sold as a plan per terminal. Starlink's business plans in the United States, for example, [charge a monthly access fee per terminal plus blocks of priority data](https://www.rvmobileinternet.com/starlink-massively-changes-priority-plan-lineup-unlimited-high-speed-data-eliminated). Prices and plans differ by country.

To compare the two, bring both to the same terms. Work out the cost per site per month over the whole contract, including equipment. Then check what each gives you in committed rate, data allowance and availability.

Also check the service is licensed where your sites are. Our [Africa connectivity map](/map/) shows each country's status for Starlink, Eutelsat OneWeb and Amazon Leo, with sources.

## Compare total cost, not price per MHz

Take two mobile operators, Alpha and Beta, in a worked example. Each needs ten 1 Mbps links for 36 months. The prices are illustrative.

| | Alpha | Beta |
| --- | --- | --- |
| Approach | Buys the cheapest price per MHz | Buys on total cost of ownership |
| Equipment | Entry-level modems | Advanced modems with adaptive coding |
| Efficiency | 1.6 bps/Hz | 2.8 bps/Hz |
| Bandwidth needed | 6.25 MHz | 3.57 MHz |
| Price per MHz per month | $2,000 | $2,500 |
| Bandwidth per month | $12,500 | $8,929 |
| Equipment | $100,000 | $180,000 |
| Total over 36 months | $550,000 | $501,429 |

Beta pays 25% more per MHz and 80% more for equipment, yet spends $48,571 less over the contract. Its better equipment also leaves room to add sites without buying as much new bandwidth.

The lesson holds whatever the prices. A low unit price can hide higher bandwidth needs, weaker availability or costs that only appear later.

## Questions to ask every supplier

1. What committed rate does each site get, and what is the burst rate and contention ratio?
2. What spectral efficiency does your price assume, and with which modem and antenna?
3. What availability is the link designed for, in which band and at which sites?
4. What does equipment cost, and who installs, maintains and replaces it?
5. What are the teleport, hub, support and licence fees, monthly and one-off?
6. What happens to price and capacity when we add sites or traffic?
7. What are the contract length, notice period and penalties for leaving early?
8. Is the service licensed in each country where we have sites?

If you are comparing offers for sites in Africa and want a second view, [tell us about your project](/services/#enquire).
