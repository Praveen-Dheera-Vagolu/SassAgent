from __future__ import annotations

import copy
import datetime
from typing import Dict, List, Optional
from backend.models import (
    BillingCycle,
    ContractTerms,
    Subscription,
    UserSeat,
)


class MockSaaSProvider:
    """
    Simulates enterprise SaaS management consoles and identity directory sync.
    Provides real-time seat querying, license updates, and closed-loop inspection.
    """

    def __init__(self) -> None:
        self._initial_data: Dict[str, Subscription] = {}
        self._subscriptions: Dict[str, Subscription] = {}
        self._seed_default_subscriptions()

    def _seed_default_subscriptions(self) -> None:
        """Seed realistic enterprise SaaS subscriptions covering TC1-TC4."""

        # TC1: Slack Enterprise (100 seats, renewal in 14 days, 18 idle seats)
        slack_users: List[UserSeat] = []
        for i in range(1, 83):
            slack_users.append(
                UserSeat(
                    user_id=f"slack_user_{i:02d}",
                    email=f"user{i:02d}@acmecorp.com",
                    name=f"Active User {i}",
                    role="Product / Eng" if i % 2 == 0 else "Operations",
                    last_active_days_ago=(i % 25) + 1,
                    activity_source="Okta SAML 2.0 & Slack API",
                )
            )
        # 18 inactive users (>= 90 days)
        for i in range(83, 101):
            slack_users.append(
                UserSeat(
                    user_id=f"slack_user_{i:02d}",
                    email=f"inactive_user{i:02d}@acmecorp.com",
                    name=f"Inactive Slack User {i}",
                    role="Contractor / Former Staff",
                    last_active_days_ago=95 + (i - 83) * 4,
                    activity_source="Okta SAML 2.0 & Slack API",
                )
            )

        slack = Subscription(
            id="sub_slack_enterprise",
            name="Slack Enterprise Grid",
            category="Team Communication",
            total_seats=100,
            cost_per_seat_monthly=32.0,
            billing_cycle=BillingCycle.ANNUAL,
            days_until_renewal=14,  # TC1: <= 30 days critical renewal window!
            contract_terms=ContractTerms(
                has_mid_term_lock=True,
                reduction_window_days_before_renewal=30,  # inside window (14 <= 30)
                auto_renew_enabled=True,
                cancellation_notice_days=14,
            ),
            users=slack_users,
            icon_slug="slack",
        )

        # TC2 & TC4: Jira Cloud (50 seats, 5 idle including dev_user_04 inactive 94 days, renewal in 18 days)
        jira_users: List[UserSeat] = []
        # 45 active users
        for i in range(1, 46):
            jira_users.append(
                UserSeat(
                    user_id=f"jira_dev_{i:02d}",
                    email=f"dev{i:02d}@acmecorp.com",
                    name=f"Engineer {i}",
                    role="Software Engineer",
                    last_active_days_ago=(i % 15) + 2,
                    activity_source="Atlassian Access SSO",
                )
            )
        # 5 idle users, specifically dev_user_04 with 94 days
        jira_users.append(
            UserSeat(
                user_id="dev_user_04",
                email="dev_user_04@acmecorp.com",
                name="David Vance (Dev)",
                role="Backend Architect",
                last_active_days_ago=94,  # TC2: explicitly 94 days inactive!
                activity_source="Atlassian Access SSO",
            )
        )
        jira_users.append(
            UserSeat(
                user_id="jira_contractor_02",
                email="contractor_alex@acmecorp.com",
                name="Alex Moran",
                role="Contractor",
                last_active_days_ago=112,
                activity_source="Atlassian Access SSO",
            )
        )
        jira_users.append(
            UserSeat(
                user_id="jira_contractor_03",
                email="contractor_pat@acmecorp.com",
                name="Pat Taylor",
                role="Contractor",
                last_active_days_ago=101,
                activity_source="Atlassian Access SSO",
            )
        )
        jira_users.append(
            UserSeat(
                user_id="jira_intern_01",
                email="intern_sam@acmecorp.com",
                name="Sam Summer",
                role="Intern (Departed)",
                last_active_days_ago=130,
                activity_source="Atlassian Access SSO",
            )
        )
        jira_users.append(
            UserSeat(
                user_id="jira_designer_05",
                email="designer_lea@acmecorp.com",
                name="Lea Ray",
                role="Design Lead",
                last_active_days_ago=92,
                activity_source="Atlassian Access SSO",
            )
        )

        jira = Subscription(
            id="sub_jira_cloud",
            name="Jira Cloud Enterprise",
            category="Issue & Project Tracking",
            total_seats=50,
            cost_per_seat_monthly=50.0,
            billing_cycle=BillingCycle.ANNUAL,
            days_until_renewal=20,  # in renewal window
            contract_terms=ContractTerms(
                has_mid_term_lock=True,
                reduction_window_days_before_renewal=30,  # inside window (20 <= 30)
                auto_renew_enabled=True,
                cancellation_notice_days=30,
            ),
            users=jira_users,
            icon_slug="jira",
        )

        # TC3: Google Workspace (50 seats, 10 idle, renewal in 210 days -> mid-term lock clause -> action DEFERRED)
        google_users: List[UserSeat] = []
        for i in range(1, 41):
            google_users.append(
                UserSeat(
                    user_id=f"gsuite_user_{i:02d}",
                    email=f"team_member_{i:02d}@acmecorp.com",
                    name=f"Workspace User {i}",
                    role="General Staff",
                    last_active_days_ago=(i % 12) + 1,
                    activity_source="Google Cloud Identity",
                )
            )
        for i in range(41, 51):
            google_users.append(
                UserSeat(
                    user_id=f"gsuite_user_{i:02d}",
                    email=f"alumni_{i:02d}@acmecorp.com",
                    name=f"Departed Staff {i}",
                    role="Former Employee",
                    last_active_days_ago=98 + (i - 41) * 10,
                    activity_source="Google Cloud Identity",
                )
            )

        google = Subscription(
            id="sub_google_workspace",
            name="Google Workspace Business Plus",
            category="Productivity & Email",
            total_seats=50,
            cost_per_seat_monthly=18.0,
            billing_cycle=BillingCycle.ANNUAL,
            days_until_renewal=210,  # TC3: Mid-term! (210 > 30 days lock)
            contract_terms=ContractTerms(
                has_mid_term_lock=True,
                reduction_window_days_before_renewal=30,  # reduction window opens 30 days before renewal
                auto_renew_enabled=True,
                cancellation_notice_days=30,
            ),
            users=google_users,
            icon_slug="google",
        )

        # Additional SaaS: GitHub Enterprise (35 seats, 2 idle, renewal in 85 days)
        github_users: List[UserSeat] = []
        for i in range(1, 34):
            github_users.append(
                UserSeat(
                    user_id=f"gh_user_{i:02d}",
                    email=f"dev_gh_{i:02d}@acmecorp.com",
                    name=f"GitHub Dev {i}",
                    role="Developer",
                    last_active_days_ago=(i % 8) + 1,
                    activity_source="GitHub Organization SSO",
                )
            )
        github_users.append(
            UserSeat(
                user_id="gh_inactive_01",
                email="consultant_rob@acmecorp.com",
                name="Rob Consultant",
                role="Contractor",
                last_active_days_ago=140,
                activity_source="GitHub Organization SSO",
            )
        )
        github_users.append(
            UserSeat(
                user_id="gh_inactive_02",
                email="consultant_sarah@acmecorp.com",
                name="Sarah Vendor",
                role="Contractor",
                last_active_days_ago=115,
                activity_source="GitHub Organization SSO",
            )
        )

        github = Subscription(
            id="sub_github_enterprise",
            name="GitHub Enterprise Cloud",
            category="Code & CI/CD",
            total_seats=35,
            cost_per_seat_monthly=21.0,
            billing_cycle=BillingCycle.ANNUAL,
            days_until_renewal=85,
            contract_terms=ContractTerms(
                has_mid_term_lock=True,
                reduction_window_days_before_renewal=30,
                auto_renew_enabled=True,
                cancellation_notice_days=30,
            ),
            users=github_users,
            icon_slug="github",
        )

        self._subscriptions = {
            slack.id: slack,
            jira.id: jira,
            google.id: google,
            github.id: github,
        }
        # Deepcopy to keep golden baseline for resets
        self._initial_data = copy.deepcopy(self._subscriptions)

    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        sub = self._subscriptions.get(subscription_id)
        if sub is None:
            return None
        return copy.deepcopy(sub)

    def list_subscriptions(self) -> List[Subscription]:
        return [copy.deepcopy(sub) for sub in self._subscriptions.values()]

    def update_seats(
        self, subscription_id: str, new_total_seats: int, deprovision_user_ids: Optional[List[str]] = None
    ) -> Subscription:
        """
        Simulate an administrative API mutation reducing license count in vendor console.
        """
        if subscription_id not in self._subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found in SaaS provider console.")

        sub = self._subscriptions[subscription_id]
        sub.total_seats = new_total_seats

        if deprovision_user_ids:
            deprovision_set = set(deprovision_user_ids)
            sub.users = [u for u in sub.users if u.user_id not in deprovision_set]

        return copy.deepcopy(sub)

    def scrape_live_console(self, subscription_id: str) -> Dict:
        """
        Closed-loop console re-read: fetches live ground truth directly from the simulated
        vendor management portal.
        """
        if subscription_id not in self._subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found.")

        sub = self._subscriptions[subscription_id]
        return {
            "status": "ONLINE",
            "subscription_id": sub.id,
            "provider_name": sub.name,
            "observed_total_seats": sub.total_seats,
            "allocated_users_count": len(sub.users),
            "active_users_90d": sub.active_user_count,
            "idle_users_90d": sub.idle_user_count,
            "days_until_renewal": sub.days_until_renewal,
            "billing_cycle": sub.billing_cycle.value,
            "rate_monthly_usd": sub.cost_per_seat_monthly,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "console_endpoint": f"https://admin.mock-saas-cloud.internal/{sub.id}/license-manager",
            "ssl_verified": True,
        }

    def reset_to_baseline(self) -> None:
        """Reset mock environment to pristine initial state for repeatable test runs."""
        self._subscriptions = copy.deepcopy(self._initial_data)


# Global singleton instance for the app
mock_saas_provider = MockSaaSProvider()
