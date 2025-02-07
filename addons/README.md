This is a nest extension module, which may later merge to core Nest capabilities.

## Goal
The goal is to suport more realistic topologies for the networks for doing more than tests. For example
1. Create a topology programmatically, assign router, nodes, interfaces and addresses.
2. Spawn routing daemons.
3. Config features over topology.

## Why
To use test for more than testing existing opensource modules. It should be possible to develop and test at the sametime.
One issue experienced with NesT is that it is a pure test platform. An end user can start, run and complete test. For example, 
when running FRR tests, lot of things happen under the wrappers (cleaning up daemons after the test is one scenario). It is not possible to 
simply leave the topology with configuration running easily. So, I think a further level of APIs will help.

Secondly, in routing, the NeST has pretty basic functionality. People starting to work with routing can benefit from more robust examples or APIs to speed up the learing curve.
Then, the question is how to achieve this?

## How

I have taken some inspiration from FRR tests (and munet) and I am leaning towards 2-pronged approach
    - First: providing configuration apis for a few features
    - Second: provisioning through YANG models for other features

This can possibly be done with the following high level architecture
```markdown

                       Modules in NeST extension
                       ┌─────────────────────┐
              NeST     ▼                     ▼
              ┌─────┐    ┌──────────────┐
   ┌──────┐   │     ---->│Topo-Extension| (clos, butterfly, full mesh, etc)
   │ Name ┼───►     │    └──────────────┘
   │ Space│   │ NeST│    ┌──────────────┐
   └──────┘   │Frame|--->│ NS-CLI mode  │ (show, clear, vtsh etc.)
              │ work│    └─|─────|────|─┘
   ┌──────┐   │     │      ▼     |    |
   │      ├───►     │    ┌──┐  ┌─▼┐   ▼┌─┐
   │FRRd  │   │     │    │  │  │  │    │ │
   └──────┘   └─────┘    └──┘  └──┘    └─┘
                       BGP-Evpn SD-WAN  BGP-basic (many more like SRv6)
                         API    API      API
```

### The existing modules in above diagram are:

- Namespaces: Basic network namespace suport on linux.
- FRRd: open source FRR installation
- NeST: NeST module

### New moduels will be

-Topo-Extension: a topology repository to create different types of simple or complex topologies (with ability to scale)
    (TBD: is it more intersting to exted current TopologyMap in NeST?)
- NS-CLI: This will help us go beyond NeST's start-run-cleanup methodology. We can create topology, addresses, interfaces, daemons, then interface with namespaces directly for any further control.
- Feature APIs: will help build features (network services) using APIs that maybe quite similar to those provides in FRR tests/topotests but unfortunately can not be used as is.


