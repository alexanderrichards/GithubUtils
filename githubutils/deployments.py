"""Module to manipulate GitHub deployments via the GitHub API."""
import os
import urlparse
import requests

__all__ = ("Repo",)


class NamedDataStore(object):
    """A named dictionary interface."""

    __slots__ = ("_data_dict",)

    def __init__(self, data_dict, required_keys=None):
        if required_keys is not None:
            if not isinstance(required_keys, set):
                required_keys = set(required_keys)
            required_keys -= data_dict.viewkeys()
            if required_keys:
                raise ValueError("%r dict missing necessary keys: %s" % (self.__class__.__name__,
                                                                         list(required_keys)))
        self._data_dict = data_dict

    def __getattr__(self, attr):
        if attr in self._data_dict:
            return self._data_dict[attr]
        raise AttributeError("%r object has no attribute %r" % (self.__class__.__name__, attr))

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           ', '.join('%s=%r' % item for item in self._data_dict.iteritems()))


class Status(NamedDataStore):
    """Class representing a GitHub deployment status."""

    __slots__ = ()

    def __repr__(self):
        return "Status(id=%d, state=%r, created_at=%r)" % (self._data_dict.get("id"),
                                                           self._data_dict.get("state"),
                                                           self._data_dict.get("created_at"))


class Deployment(NamedDataStore):
    """Class representing a GitHub deployment."""

    __slots__ = ("_auth",)

    def __init__(self, deployment_dict, auth=None):
        super(Deployment, self).__init__(deployment_dict, {"statuses_url"})
        self._auth = auth
        
    def statuses(self, id=None):
        """List deployment statuses."""
        url = self._data_dict["statuses_url"]
        if id is not None:
            url = os.path.join(url, str(id))
        statuses = requests.get(url, auth=self._auth).json()
        if not isinstance(statuses, list):
            return Status(statuses)
        return [Status(status) for status in statuses]

    def create_status(self, state, **kwargs):
        """Create new status."""
        valid_states = ('error', 'failure', 'pending', 'success')
        if state not in valid_states:
            raise ValueError("Invalid state, expected on of %s, got %r" % (valid_states, state))
        kwargs['state'] = state
        request = requests.post(self._data_dict["statuses_url"], auth=self._auth, json=kwargs)
        request.raise_for_status()
        return Status(request.json())

    def __repr__(self):
        return "Deployment(id=%d, ref=%r, environment=%r, description=%r)"\
               % (self._data_dict.get("id"), self._data_dict.get("ref"),
                  self._data_dict.get("environment"), self._data_dict.get("description"))


class Repo(object):
    """
    A GitHub Repo.

    This is used as the starting point for dealing with GitHub deployments.

    Example:
        r = Repo("https://github.com/<username/organisation>/<repo>", ("<username>", "<password>"))

        r.deployments()  # This will list all deployments
        r.deployments()[0].statuses()  # This will list the statuses for given deployment from list.
        r.deployments(1234).statuses()  # This will list the statuses for given deployment
        r.deployments(1234).statuses(1234)  # This will return the given status for given deployment

        # Can create new deployments easily
        new_deployment = r.create_deployment("<ref>")
        new_deployment.create_status("pending")
    """

    __slots__ = ("_deployment_api_url", "_auth")

    def __init__(self, url, auth=None):
        """
        Instantiate a Repo object.

        Args:
            url (str): The URL of the GitHub repo.
            auth (None/(str, str)): The auth tuple containing ("username", "password") as strings.
                                    This parameter is passed on directly to the underlying requests
                                    method.
        """
        url_parsed = urlparse.urlparse(url)
        url_parsed = url_parsed._replace(netloc='.'.join(['api', url_parsed.netloc]),
                                         path=os.path.join('/repos',
                                                           url_parsed.path.lstrip('/'),
                                                           'deployments'))
        self._deployment_api_url = urlparse.urlunparse(url_parsed)
        self._auth = auth

    def deployments(self, id=None, **kwargs):
        """
        List deployments for this repo.

        Args:
            id (None/int/str): The id of the deployment to return. If None then all deployments are
                                returned.

        Keyword Args:
            These are passed as json data to the GitHub API.

        Returns:
            Deployment/[Deployment]: The requested (or all) deployments for the current repo.
        """
        url = self._deployment_api_url
        if id is not None:
            url = os.path.join(url, str(id))
        deployments = requests.get(url,
                                   auth=self._auth,
                                   json=kwargs).json()

        if not isinstance(deployments, list):
            return Deployment(deployments, auth=self._auth)
        return [Deployment(deployment, auth=self._auth) for deployment in deployments]

    def create_deployment(self, ref, **kwargs):
        """Create a new deployment."""
        kwargs['ref'] = ref
        request = requests.post(self._deployment_api_url,
                                auth=self._auth,
                                json=kwargs)
        request.raise_for_status()
        return Deployment(request.json(), auth=self._auth)
