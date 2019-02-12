import os
import urlparse
import requests

__all__ = ("Repo",)


class Status(object):
    def __init__(self, status_dict):
        self._status_dict = status_dict

    def __getattr__(self, attr):
        if attr in self._status_dict:
            return self._status_dict[attr]
        raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, attr))
    
    def __repr__(self):
        return "Status(id=%d, state=%r, created_at=%r)" % (self.id, self.state, self.created_at)

class Deployment(object):
    def __init__(self, deployment_dict, auth=None):
        self._deployment_dict = deployment_dict
        self._auth = auth
        
    def __getattr__(self, attr):
        if attr in self._deployment_dict:
            return self._deployment_dict[attr]
        raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, attr))

    def statuses(self, id=None):
        url = self.statuses_url
        if isinstance(id, (int, basestring)):
            url = os.path.join(url, str(id))
        statuses = requests.get(url, auth=self._auth).json()
        if not isinstance(statuses, list):
            return Status(statuses)
        return [Status(status) for status in statuses]

    def create_status(self, state, **kwargs):
        valid_states = ('error', 'failure', 'pending', 'success')
        if state not in valid_states:
            raise ValueError("Invalid state, expected on of %s, got %r" % (valid_states, state))
        kwargs['state'] = state
        request = requests.post(self.statuses_url, auth=self._auth, json=kwargs)
        request.raise_for_status()
        return Status(request.json())

    def __repr__(self):
        return "Deployment(id=%d, ref=%r, environment=%r, description=%r)"\
            % (self.id, self.ref, self.environment, self.description)

class Repo(object):
    def __init__(self, url, auth=None):
        url_parsed = urlparse.urlparse(url)
        url_parsed = url_parsed._replace(netloc='.'.join(['api', url_parsed.netloc]),
                                         path=os.path.join('/repos',
                                                           url_parsed.path.lstrip('/'),
                                                           'deployments'))
        self._deployment_api_url = urlparse.urlunparse(url_parsed)
        self._auth = auth

    def deployments(self, id=None, **kwargs):
        url = self._deployment_api_url
        if isinstance(id, (int, basestring)):
            url = os.path.join(url, str(id))
        deployments = requests.get(url,
                                   auth=self._auth,
                                   json=kwargs).json()

        if not isinstance(deployments, list):
            return Deployment(deployments, auth=self._auth)
        return [Deployment(deployment, auth=self._auth) for deployment in deployments]

    def create_deployment(self, ref, **kwargs):
        kwargs['ref'] = ref
        request = requests.post(self._deployment_api_url,
                                auth=self._auth,
                                json=kwargs)
        request.raise_for_status()
        return Deployment(request.json(), auth=self._auth)
