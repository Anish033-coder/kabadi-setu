// Cedar decides who may attempt an action. Whether it is valid right now
// (status, version, expiry) is enforced by the transition rules in backend/domain.py.
permit(principal is Household, action in [Action::"view", Action::"cancel", Action::"collect"], resource is Request)
when { resource.owner == principal };

permit(principal is PickupLink, action in [Action::"view", Action::"accept", Action::"reject", Action::"collect"], resource is Request)
when { principal.requestId == resource.requestId };
