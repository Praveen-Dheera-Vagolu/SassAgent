import * as cheerio from 'cheerio';
import { db } from './db.js';

/**
 * Cheerio-based Web Scraper & HTML Parser for Mock Admin Consoles
 * Implements the brief's suggested tool: HTTP Request + Cheerio to extract
 * seat counts, user activity rows, and renewal dates directly from mock admin HTML pages.
 */
export class AdminConsoleScraper {

  /**
   * Generates mock SaaS Admin Billing HTML page
   */
  static generateBillingHtml(tool) {
    const diffDays = Math.ceil((new Date(tool.renewal_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    return `
      <!DOCTYPE html>
      <html>
        <head><title>${tool.name} Admin Console - License Management</title></head>
        <body>
          <div id="admin-portal" data-tool-id="${tool.id}">
            <h1 class="vendor-header">${tool.name} Management Console</h1>
            <div class="billing-summary-card">
              <span class="plan-cycle">${tool.billing_cycle}</span>
              <span class="license-allocated" data-seats="${tool.total_licenses}">${tool.total_licenses} Seats</span>
              <span class="renewal-info" data-renewal-date="${tool.renewal_date}">${tool.renewal_date} (${diffDays} days remaining)</span>
              <span class="monthly-unit-rate" data-rate="${tool.cost_per_seat_monthly}">$${tool.cost_per_seat_monthly}/seat/mo</span>
              <span class="annual-unit-rate" data-rate="${tool.cost_per_seat_annual}">$${tool.cost_per_seat_annual}/seat/yr</span>
              <div class="contract-flags" data-midterm-lock="${tool.contract_has_mid_term_lock}" data-autorenew="${tool.auto_renew_enabled}"></div>
            </div>
          </div>
        </body>
      </html>
    `;
  }

  /**
   * Generates mock SaaS Admin User Directory HTML page
   */
  static generateUserDirectoryHtml(toolId, users) {
    const rows = users.map(u => {
      const daysInactive = Math.floor((Date.now() - new Date(u.last_active_timestamp).getTime()) / (1000 * 60 * 60 * 24));
      return `
        <tr class="user-row" id="user-${u.id}" data-user-id="${u.id}" data-email="${u.user_email}" data-role="${u.role}">
          <td class="email-col">${u.user_email}</td>
          <td class="role-col">${u.role}</td>
          <td class="last-active-col" data-timestamp="${u.last_active_timestamp}">${u.last_active_timestamp}</td>
          <td class="inactivity-days" data-days="${daysInactive}">${daysInactive} days ago</td>
          <td class="status-col">${daysInactive >= 90 ? 'IDLE' : 'ACTIVE'}</td>
        </tr>
      `;
    }).join('\n');

    return `
      <!DOCTYPE html>
      <html>
        <head><title>User Directory - ${toolId}</title></head>
        <body>
          <table id="user-directory-table" data-tool-id="${toolId}" data-total="${users.length}">
            <thead>
              <tr><th>Email</th><th>Role</th><th>Last Login</th><th>Inactivity</th><th>Status</th></tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </body>
      </html>
    `;
  }

  /**
   * Scrapes billing page using Cheerio to extract structured licensing data
   */
  static scrapeBillingPage(htmlString, sourceUrl) {
    const $ = cheerio.load(htmlString);
    const toolId = $('#admin-portal').attr('data-tool-id');
    const toolName = $('.vendor-header').text().replace(' Management Console', '').trim();
    const totalLicenses = parseInt($('.license-allocated').attr('data-seats') || '0', 10);
    const renewalDate = $('.renewal-info').attr('data-renewal-date');
    const monthlyRate = parseFloat($('.monthly-unit-rate').attr('data-rate') || '0');
    const billingCycle = $('.plan-cycle').text().trim();
    const hasMidTermLock = $('.contract-flags').attr('data-midterm-lock') === '1' || $('.contract-flags').attr('data-midterm-lock') === 'true';

    return {
      source_url: sourceUrl,
      retrieval_timestamp: new Date().toISOString(),
      extractor: 'Cheerio v1.0.0 HTML Scraper',
      tool_id: toolId,
      tool_name: toolName,
      total_licenses: totalLicenses,
      renewal_date: renewalDate,
      cost_per_seat_monthly: monthlyRate,
      billing_cycle: billingCycle,
      has_mid_term_lock: hasMidTermLock
    };
  }

  /**
   * Scrapes user directory page using Cheerio to extract individual accounts & inactivity
   */
  static scrapeUserDirectoryPage(htmlString, sourceUrl) {
    const $ = cheerio.load(htmlString);
    const toolId = $('#user-directory-table').attr('data-tool-id');
    const users = [];

    $('.user-row').each((_, el) => {
      const id = $(el).attr('data-user-id');
      const email = $(el).attr('data-email');
      const role = $(el).attr('data-role');
      const lastActive = $(el).find('.last-active-col').attr('data-timestamp');
      const daysInactive = parseInt($(el).find('.inactivity-days').attr('data-days') || '0', 10);

      users.push({
        id,
        email,
        role,
        last_active_timestamp: lastActive,
        days_inactive: daysInactive,
        is_idle: daysInactive >= 90
      });
    });

    return {
      source_url: sourceUrl,
      retrieval_timestamp: new Date().toISOString(),
      extractor: 'Cheerio v1.0.0 HTML Scraper',
      tool_id: toolId,
      total_extracted_users: users.length,
      idle_users_count: users.filter(u => u.is_idle).length,
      users
    };
  }
}
