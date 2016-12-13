from jsonrpc import JsonRpcServer
import jsonrpc
import database as d


class CrwJsonRpc(JsonRpcServer):
    def __init__(self, database):
        self.udb = d.UserDatabase(database)
        self.tdb = d.TeamDatabase(database)
        self.sdb = d.SessionDatabase(database)

    def echo(self, s):
        return s

    def create_account(self, email, password):
        try:
            self.udb.add_user(email, password)
            return True
        except d.PasswordFieldEmpty, e:
            raise error_no_password_submitted
        except d.UserDoesNotExistError, e:
            raise error_account_already_exists

    def login(self, email, password):
        """This function will verify the user and return a new session
        key if the user has been authencitated correctly."""
        if (not self.udb.does_user_email_exist(email)) or\
           (not self.udb.verify_user(email, password)):
            raise error_invalid_account_credentials

        return self.sdb.generate_session_key(
            self.udb.get_user_id(email))

    def create_team(self, team_name, user_id, session_key):
        """Creates a team with the user of user_id as an coach.
        Returns the team_id of the created team."""
        if not self.sdb.verify_session_key(user_id, session_key):
            raise error_invalid_session_key

        return self.tdb.create_team(user_id, team_name)

    def add_to_team(self, user_to_add_id, user_id, session_key):
        """Adds the user with user_to_add_id to the team that user_id
        is in."""
        if not self.sdb.verify_session_key(user_id, session_key):
            raise error_invalid_session_key

        (team_id, coach) = self.udb.get_user_team_status(user_id)
        if (team_id is None or coach is None or not coach):
            raise error_invalid_action_no_coach

        self.tdb.add_user_to_team(user_id, user_to_add_id)

        return True
    
    def team_info(self, user_id, session_key):
        """Returns the team id, team name and members with user id, email and coach status."""
        if not self.sdb.verify_session_key(user_id, session_key):
            raise error_invalid_session_key
        
        (team_id, coach) = self.udb.get_user_team_status(user_id)
        if (team_id is None):
            raise error_user_is_not_in_a_team
        
        team_name = self.tdb.get_team_name(team_id)
        team_members = self.tdb.get_team_members(team_id)
        return [team_id, team_name] + team_members

    
error_account_already_exists = jsonrpc.RPCError(
    1, """There is already an account associated
    with this email""")
error_invalid_account_credentials = jsonrpc.RPCError(
    2, """The provided credentials are incorrect""")
error_invalid_session_key = jsonrpc.RPCError(
    3, """The provided session key is incorrect or expired""")
error_no_password_submitted = jsonrpc.RPCError(
    4, """No password is entered""")
error_invalid_action_no_coach = jsonrpc.RPCError(
    5, """The user is not a coach in a team, so they can't perform
    this action""")
error_user_is_not_in_a_team = jsonrpc.RPCError(
    6, """The user is not in a team""")
