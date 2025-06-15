# Users

Types:

```python
from earn_app.types import User, UserListMissionsResponse, UserListReferralsResponse
```

Methods:

- <code title="post /users">client.users.<a href="./src/earn_app/resources/users/users.py">create</a>(\*\*<a href="src/earn_app/types/user_create_params.py">params</a>) -> <a href="./src/earn_app/types/user.py">User</a></code>
- <code title="get /users/{userId}/missions">client.users.<a href="./src/earn_app/resources/users/users.py">list_missions</a>(user_id) -> <a href="./src/earn_app/types/user_list_missions_response.py">UserListMissionsResponse</a></code>
- <code title="get /users/{userId}/referrals">client.users.<a href="./src/earn_app/resources/users/users.py">list_referrals</a>(user_id) -> <a href="./src/earn_app/types/user_list_referrals_response.py">UserListReferralsResponse</a></code>
- <code title="get /users/wallet/{address}">client.users.<a href="./src/earn_app/resources/users/users.py">retrieve_by_wallet</a>(address) -> <a href="./src/earn_app/types/user.py">User</a></code>

## Stakes

Types:

```python
from earn_app.types.users import UserStake, StakeListResponse
```

Methods:

- <code title="post /users/{userId}/stakes">client.users.stakes.<a href="./src/earn_app/resources/users/stakes.py">create</a>(user_id, \*\*<a href="src/earn_app/types/users/stake_create_params.py">params</a>) -> <a href="./src/earn_app/types/users/user_stake.py">UserStake</a></code>
- <code title="get /users/{userId}/stakes">client.users.stakes.<a href="./src/earn_app/resources/users/stakes.py">list</a>(user_id) -> <a href="./src/earn_app/types/users/stake_list_response.py">StakeListResponse</a></code>

# Missions

Types:

```python
from earn_app.types import Mission, MissionListResponse
```

Methods:

- <code title="get /missions/{id}">client.missions.<a href="./src/earn_app/resources/missions.py">retrieve</a>(id) -> <a href="./src/earn_app/types/mission.py">Mission</a></code>
- <code title="get /missions">client.missions.<a href="./src/earn_app/resources/missions.py">list</a>(\*\*<a href="src/earn_app/types/mission_list_params.py">params</a>) -> <a href="./src/earn_app/types/mission_list_response.py">MissionListResponse</a></code>

# Staking

Types:

```python
from earn_app.types import StakingVault, StakingListVaultsResponse
```

Methods:

- <code title="get /staking/vaults">client.staking.<a href="./src/earn_app/resources/staking.py">list_vaults</a>() -> <a href="./src/earn_app/types/staking_list_vaults_response.py">StakingListVaultsResponse</a></code>

# Stats

Types:

```python
from earn_app.types import StatRetrieveResponse
```

Methods:

- <code title="get /stats">client.stats.<a href="./src/earn_app/resources/stats.py">retrieve</a>() -> <a href="./src/earn_app/types/stat_retrieve_response.py">StatRetrieveResponse</a></code>

# Token

Types:

```python
from earn_app.types import TokenRetrieveInfoResponse
```

Methods:

- <code title="get /token/info">client.token.<a href="./src/earn_app/resources/token.py">retrieve_info</a>() -> <a href="./src/earn_app/types/token_retrieve_info_response.py">TokenRetrieveInfoResponse</a></code>
