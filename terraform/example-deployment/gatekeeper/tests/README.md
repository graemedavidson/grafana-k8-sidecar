# Gatekeeper Constraint tests

Create test namespace.

```
kubectl create ns developers
kubectl label ns developers "example.co.uk/team"="developers"
```

Add a dashboard resource pointing to a dir not found in [rules](../constraint_developers.yml).
