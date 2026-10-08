permit(principal is Household, action, resource is Request)
when { resource.owner == principal };

permit(principal is PickupLink, action, resource is Request)
when {
    principal.requestId == resource.requestId &&
    context.linkValid &&
    action in [Action::"view", Action::"accept", Action::"reject", Action::"collect"]
};
