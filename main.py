import threading
from flask import Flask

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Bot is running!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()

# BezGranicVPN — полный код проекта

BOT_CODE = r"""
import { Telegraf, session, Context } from "telegraf";
import { logger } from "./lib/logger";

interface SessionData {
  pendingPlan: string | null;
  subscriptionUntil: string | null;
  balance: number;
}
type BotContext = Context & { session: SessionData };

const PLANS = [
  { id: "month_1", name: "1 месяц", price: 70, stars: 70, usdt: 0.91, description: "1 месяц доступа к BezGranicVPN", duration_days: 30, emoji: "🗓️" },
];

const PRIVACY_POLICY_URL = "https://telegra.ph/Politika-konfidencialnosti-04-01-26";
const USER_AGREEMENT_URL  = "https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19";
const SUPPORT_BOT         = "BezGranicSupportbot";
const CHANNEL_USERNAME    = "BezGranicVPN";

function getWebAppUrl(): string | null {
  const domains = process.env.REPLIT_DOMAINS;
  if (domains) return "https://" + domains.split(",")[0].trim();
  return null;
}

function getPlanById(id: string) { return PLANS.find(p => p.id === id) || null; }

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function mainMenuText(ctx: BotContext): string {
  const userId = ctx.from?.id ?? 0;
  const balance = ctx.session.balance ?? 0;
  const sub = ctx.session.subscriptionUntil;
  const subStatus = sub
    ? `🟢 Активна до ${formatDate(sub)}`
    : "🔴 Не активна";
  return (
    "🔥 <b>BezGranicVPN</b>\n" +
    "Главное меню\n" +
    `ID: <code>${userId}</code>\n` +
    "━━━━━━━━━━━━━━━━━\n" +
    `💲 Баланс: <b>${balance.toFixed(2)} ₽</b>\n` +
    "📊 Статус подписки\n" +
    `${subStatus}\n` +
    "━━━━━━━━━━━━━━━━━"
  );
}

function mainMenuKeyboard() {
  const url = getWebAppUrl();
  const lkButton: any = url
    ? { text: "Личный кабинет", web_app: { url } }
    : { text: "Личный кабинет", callback_data: "profile" };
  return { reply_markup: { inline_keyboard: [
    [{ text: "💎 Купить подписку", callback_data: "show_plans" }],
    [
      { text: "👥 Пригласить друга", callback_data: "referral" },
      { text: "💬 Поддержка",        url: `https://t.me/${SUPPORT_BOT}` },
    ],
    [lkButton],
    [{ text: "💰 Пополнить баланс",  callback_data: "topup" }],
  ]}};
}

function plansInlineKeyboard() {
  const url = getWebAppUrl();
  const btns: any[][] = PLANS.map(p => [{
    text: `${p.emoji} ${p.name} | ${p.price} рублей ♾️`,
    callback_data: `plan_${p.id}`,
  }]);
  if (url) btns.push([{ text: "🌍 Открыть приложение", web_app: { url } }]);
  btns.push([{ text: "← Назад", callback_data: "main_menu" }]);
  return { reply_markup: { inline_keyboard: btns } };
}

function paymentMethodKeyboard(plan: typeof PLANS[0]) {
  return { reply_markup: { inline_keyboard: [
    [{ text: `⭐ Telegram Stars — ${plan.stars}`, callback_data: `pay_stars_${plan.id}` }],
    [{ text: `💲 USDT — ${plan.usdt}`,           callback_data: `pay_usdt_${plan.id}`  }],
    [{ text: "← Назад", callback_data: "show_plans" }],
  ]}};
}

function backToMainKeyboard() {
  return { reply_markup: { inline_keyboard: [[{ text: "← В главное меню", callback_data: "main_menu" }]] }};
}

const choosePlanText =
  "💰 <b>Доступные тарифы:</b>\n\n" +
  PLANS.map(p => `${p.emoji} ${p.name} | ${p.price} рублей ♾️`).join("\n") +
  "\n\n👇 Нажмите на тариф для оплаты";

export function startBot() {
  const token = process.env.BOT_TOKEN;
  if (!token) { logger.warn("BOT_TOKEN не задан — бот не запущен"); return; }

  const bot = new Telegraf<BotContext>(token);
  bot.use(session({ defaultSession: (): SessionData => ({ pendingPlan: null, subscriptionUntil: null, balance: 0 }) }));

  bot.telegram.setMyCommands([
    { command: "start",  description: "🏠 Главное меню" },
    { command: "help",   description: "❓ Помощь и поддержка" },
    { command: "policy", description: "📜 Политика конфиденциальности" },
    { command: "terms",  description: "📋 Пользовательское соглашение" },
  ]).catch(() => {});

  bot.telegram.setChatMenuButton({ menuButton: { type: "default" } }).catch(() => {});

  // Убираем нижнюю клавиатуру — все кнопки только на экране (inline)
  bot.start(async ctx => {
    // Принудительно убираем старую нижнюю клавиатуру
    const tmp = await ctx.reply("⏳", { reply_markup: { remove_keyboard: true } } as any);
    await ctx.deleteMessage(tmp.message_id).catch(() => {});
    await ctx.reply(mainMenuText(ctx), { parse_mode: "HTML", ...mainMenuKeyboard() } as any);
  });

  bot.action("main_menu", async ctx => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(mainMenuText(ctx), { parse_mode: "HTML", ...mainMenuKeyboard() } as any).catch(async () => {
      await ctx.reply(mainMenuText(ctx), { parse_mode: "HTML", ...mainMenuKeyboard() } as any);
    });
  });

  bot.action("show_plans", async ctx => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(choosePlanText, { parse_mode: "HTML", ...plansInlineKeyboard() } as any).catch(async () => {
      await ctx.reply(choosePlanText, { parse_mode: "HTML", ...plansInlineKeyboard() } as any);
    });
  });

  bot.action("profile", async ctx => {
    await ctx.answerCbQuery();
    const sub = ctx.session.subscriptionUntil;
    const subStatus = sub ? `🟢 Активна до <b>${formatDate(sub)}</b>` : "🔴 Не активна";
    await ctx.editMessageText(
      `👤 <b>Личный кабинет</b>\n\n` +
      `🆔 ID: <code>VPN-${ctx.from!.id}</code>\n` +
      `💲 Баланс: <b>${(ctx.session.balance ?? 0).toFixed(2)} ₽</b>\n` +
      `📊 Подписка: ${subStatus}`,
      { parse_mode: "HTML", ...backToMainKeyboard() } as any
    ).catch(() => {});
  });

  bot.action("topup", async ctx => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(
      "💰 <b>Пополнение баланса</b>\n\nДля пополнения баланса свяжитесь с поддержкой.",
      { parse_mode: "HTML", reply_markup: { inline_keyboard: [
        [{ text: "📩 Написать в поддержку", url: `https://t.me/${SUPPORT_BOT}` }],
        [{ text: "← В главное меню", callback_data: "main_menu" }],
      ]}}
    ).catch(() => {});
  });

  bot.action("referral", async ctx => {
    await ctx.answerCbQuery();
    const refLink = `https://t.me/BezGranicVPN_bot?start=ref_${ctx.from!.id}`;
    await ctx.editMessageText(
      "🎁 <b>Реферальная программа</b>\n\n" +
      "При регистрации по вашей ссылке вы и ваш друг получаете по <b>15 ₽</b>\n" +
      "Далее вы получаете <b>20%</b> с каждого пополнения приглашённого\n\n" +
      "👥 Приглашено: <b>0 чел.</b>\n\n" +
      "🔗 Ваша ссылка:\n" +
      `<code>${refLink}</code>`,
      { parse_mode: "HTML", ...backToMainKeyboard() } as any
    ).catch(() => {});
  });

  bot.action("instruction", async ctx => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(
      "📖 <b>Инструкция по подключению</b>\n\n" +
      "<b>1.</b> Скачайте приложение <b>V2RayTun</b>\n\n" +
      "<b>2.</b> Перейдите в «👤 Личный кабинет» и скопируйте ключ\n\n" +
      "<b>3.</b> В V2RayTun нажмите «Вставить из буфера» — готово!",
      { parse_mode: "HTML", reply_markup: { inline_keyboard: [
        [
          { text: "🤖 Android", url: "https://play.google.com/store/apps/details?id=com.v2raytun.android" },
          { text: "🍎 iPhone",  url: "https://apps.apple.com/app/v2raytun/id6476628951" },
        ],
        [{ text: "← В главное меню", callback_data: "main_menu" }],
      ]}}
    ).catch(() => {});
  });

  bot.action("docs", async ctx => {
    await ctx.answerCbQuery();
    await ctx.editMessageText("📜 <b>Документы сервиса</b>", { parse_mode: "HTML", reply_markup: { inline_keyboard: [
      [{ text: "📜 Политика конфиденциальности", url: PRIVACY_POLICY_URL }],
      [{ text: "📋 Пользовательское соглашение", url: USER_AGREEMENT_URL }],
      [{ text: "← В главное меню", callback_data: "main_menu" }],
    ]}}).catch(() => {});
  });

  bot.action(/^plan_(.+)$/, async ctx => {
    await ctx.answerCbQuery();
    const plan = getPlanById(ctx.match[1]);
    if (!plan) return;
    ctx.session.pendingPlan = ctx.match[1];
    await ctx.editMessageText(
      `💳 <b>Способ оплаты</b>\n\n` +
      `Тариф: <b>${plan.emoji} ${plan.name}</b>\n` +
      `Цена: <b>${plan.price} ₽</b>\n` +
      `• Stars: <b>${plan.stars} ⭐</b>\n` +
      `• USDT: <b>${plan.usdt}</b>`,
      { parse_mode: "HTML", ...paymentMethodKeyboard(plan) } as any
    );
  });

  bot.action(/^pay_stars_(.+)$/, async ctx => {
    await ctx.answerCbQuery();
    const plan = getPlanById(ctx.match[1]);
    if (!plan) return;
    await ctx.deleteMessage().catch(() => {});
    await ctx.replyWithInvoice({
      title: `BezGranicVPN — ${plan.name}`,
      description: plan.description,
      payload: `stars_${plan.id}_${ctx.from!.id}`,
      currency: "XTR",
      prices: [{ label: plan.name, amount: plan.stars }],
    });
  });

  bot.action(/^pay_usdt_(.+)$/, async ctx => {
    await ctx.answerCbQuery();
    const planId = ctx.match[1];
    await ctx.editMessageText(
      "💲 <b>Оплата USDT</b>\n\nОбратитесь в поддержку — предоставим актуальный адрес кошелька.",
      { parse_mode: "HTML", reply_markup: { inline_keyboard: [
        [{ text: "📩 Написать в поддержку", url: `https://t.me/${SUPPORT_BOT}` }],
        [{ text: "← Назад", callback_data: `plan_${planId}` }],
      ]}}
    );
  });

  bot.on("pre_checkout_query", async ctx => { await ctx.answerPreCheckoutQuery(true); });

  bot.on("successful_payment", async ctx => {
    const payment = ctx.message!.successful_payment!;
    const parts   = payment.invoice_payload.split("_");
    const plan    = getPlanById(parts[1] + "_" + parts[2]);

    // Автоматически рассчитываем дату окончания подписки
    if (plan) {
      const now = new Date();
      const current = ctx.session.subscriptionUntil ? new Date(ctx.session.subscriptionUntil) : now;
      const base = current > now ? current : now;
      const until = new Date(base);
      until.setDate(until.getDate() + plan.duration_days);
      ctx.session.subscriptionUntil = until.toISOString();
    }

    logger.info({ userId: ctx.from!.id, planId: plan?.id, stars: payment.total_amount }, "[Stars] Оплата");
    await ctx.reply(
      `✅ <b>Оплата прошла успешно!</b>\n\n` +
      `Тариф: <b>${plan ? plan.emoji + " " + plan.name : "—"}</b>\n` +
      `Оплачено: <b>${payment.total_amount} ⭐</b>\n` +
      (ctx.session.subscriptionUntil ? `\n📅 Подписка активна до: <b>${formatDate(ctx.session.subscriptionUntil)}</b>\n` : "") +
      `\nПодписка активирована!`,
      { parse_mode: "HTML", ...backToMainKeyboard() } as any
    );
  });

  bot.command("policy", async ctx => { await ctx.reply("📜 " + PRIVACY_POLICY_URL); });
  bot.command("terms",  async ctx => { await ctx.reply("📋 " + USER_AGREEMENT_URL); });
  bot.command("help",   async ctx => {
    await ctx.reply(
      "❓ <b>Помощь и поддержка</b>\n\nЕсли возникли вопросы — поддержка готова помочь.\n\n⏰ 9:00–21:00 МСК",
      { parse_mode: "HTML", reply_markup: { inline_keyboard: [
        [{ text: "📩 Написать в поддержку", url: `https://t.me/${SUPPORT_BOT}` }],
        [{ text: "← В главное меню", callback_data: "main_menu" }],
      ]}}
    );
  });

  bot.catch((err: unknown, ctx) => { logger.error({ err, updateType: ctx.updateType }, "Ошибка бота"); });

  const launchWithRetry = async (max = 30) => {
    for (let i = 0; i < max; i++) {
      try {
        await bot.launch({ dropPendingUpdates: true });
        logger.info("✅ VPN Бот запущен!");
        return;
      } catch (err: any) {
        if (err?.response?.error_code === 409 || err?.message?.includes("409")) {
          const delay = Math.min((i + 1) * 3000, 15000);
          logger.warn({ attempt: i + 1 }, `Конфликт 409, повтор через ${delay / 1000}с...`);
          await new Promise(r => setTimeout(r, delay));
        } else throw err;
      }
    }
    throw new Error("Не удалось запустить бота");
  };

  launchWithRetry().catch(err => { logger.error({ err }, "Критическая ошибка запуска бота"); });
  process.once("SIGINT",  () => bot.stop("SIGINT"));
  process.once("SIGTERM", () => bot.stop("SIGTERM"));
  logger.info("VPN Бот инициализируется...");
}

"""

MINI_APP_CODE = r"""
import { useState, useEffect } from "react";

const PLANS = [
  { id: "month_1", name: "1 месяц",  price: 70,  stars: 70,  usdt: 0.91, days: 30,  emoji: "🌙" },
  { id: "month_3", name: "3 месяца", price: 180, stars: 180, usdt: 2.33, days: 90,  emoji: "⭐" },
  { id: "year_1",  name: "1 год",    price: 590, stars: 590, usdt: 7.65, days: 365, emoji: "💎" },
];

type Tab = "home" | "payment" | "referral" | "profile";

export default function Home() {
  const tg = (window as any).Telegram?.WebApp;
  const [activeTab, setActiveTab] = useState<Tab>("home");
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, []);

  const tgUser     = tg?.initDataUnsafe?.user;
  const firstName  = tgUser?.first_name  || "Пользователь";
  const username   = tgUser?.username    || "";
  const userId     = tgUser?.id ?? 0;
  const displayName = username ? `@${username}` : firstName;
  const userIdStr  = userId ? String(userId) : "—";
  const refCode    = `REF-${String(userId || "0000").slice(-4).toUpperCase()}-BGV`;
  const refLink    = `https://t.me/BezGranicVPN_bot?start=${refCode}`;

  const copyRef = () => {
    navigator.clipboard.writeText(refLink).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="app-root">
      <div className="bg-orb bg-orb-1" />
      <div className="bg-orb bg-orb-2" />
      <div className="bg-orb bg-orb-3" />

      <div className="content-wrap">
        {activeTab === "home" && <HomeTab displayName={displayName} />}
        {activeTab === "payment" && (
          <PaymentTab
            selectedPlan={selectedPlan}
            setSelectedPlan={setSelectedPlan}
            userId={userId}
          />
        )}
        {activeTab === "referral" && (
          <ReferralTab refCode={refCode} refLink={refLink} copied={copied} copyRef={copyRef} />
        )}
        {activeTab === "profile" && (
          <ProfileTab
            displayName={displayName}
            userIdStr={userIdStr}
            refCode={refCode}
          />
        )}
      </div>

      <nav className="bottom-nav">
        {([
          { id: "home",     icon: "🏠", label: "Главная"  },
          { id: "payment",  icon: "💳", label: "Тарифы"   },
          { id: "referral", icon: "🔗", label: "Рефералы" },
          { id: "profile",  icon: "👤", label: "Профиль"  },
        ] as { id: Tab; icon: string; label: string }[]).map(tab => (
          <button
            key={tab.id}
            className={`nav-btn ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span className="nav-icon">{tab.icon}</span>
            <span className="nav-label">{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

function HomeTab({ displayName }: { displayName: string }) {
  return (
    <div className="tab-content">
      <div className="hero-section">
        <div className="logo-glow">🛡️</div>
        <h1 className="hero-title">BEZGRANICVPN</h1>
        <p className="hero-sub">Привет, {displayName}! 👋</p>
        <p className="hero-desc">Надёжная защита вашего интернет-соединения</p>
      </div>

      <div className="glass-card amber-card">
        <div className="card-row">
          <span className="card-label">Подписка</span>
          <span className="badge-inactive">Не активна</span>
        </div>
        <div className="card-divider" />
        <div className="card-row">
          <span className="card-label">Трафик</span>
          <span className="card-value">— ГБ</span>
        </div>
        <div className="card-row">
          <span className="card-label">Баланс</span>
          <span className="card-value">0 ₽</span>
        </div>
      </div>

      <div className="features-grid">
        {[
          { icon: "🔒", text: "Шифрование трафика" },
          { icon: "⚡", text: "Высокая скорость" },
          { icon: "📱", text: "Все устройства" },
          { icon: "🕐", text: "Поддержка 24/7" },
        ].map(f => (
          <div key={f.icon} className="feature-item glass-card-sm">
            <span className="feature-icon">{f.icon}</span>
            <span className="feature-text">{f.text}</span>
          </div>
        ))}
      </div>

      <a
        href="https://t.me/BezGranicSupportbot"
        target="_blank"
        rel="noreferrer"
        className="support-link"
      >
        📩 Написать в поддержку
      </a>
    </div>
  );
}

function PaymentTab({
  selectedPlan,
  setSelectedPlan,
  userId,
}: {
  selectedPlan: string | null;
  setSelectedPlan: (id: string | null) => void;
  userId: number;
}) {
  const [payMethod, setPayMethod] = useState<"stars" | "usdt" | null>(null);
  const plan = PLANS.find(p => p.id === selectedPlan);

  const handleStarsPay = () => {
    const tg = (window as any).Telegram?.WebApp;
    if (tg && plan) {
      tg.openInvoice(`https://t.me/BezGranicVPN_bot?start=pay_stars_${plan.id}`);
    } else {
      window.open(`https://t.me/BezGranicVPN_bot`, "_blank");
    }
  };

  return (
    <div className="tab-content">
      <h2 className="section-title">Тарифные планы</h2>

      <div className="plans-list">
        {PLANS.map(p => (
          <button
            key={p.id}
            className={`plan-card glass-card ${selectedPlan === p.id ? "plan-selected" : ""}`}
            onClick={() => { setSelectedPlan(p.id); setPayMethod(null); }}
          >
            <div className="plan-header">
              <span className="plan-emoji">{p.emoji}</span>
              <span className="plan-name">{p.name}</span>
              {selectedPlan === p.id && <span className="plan-check">✓</span>}
            </div>
            <div className="plan-prices">
              <span className="plan-price-main">{p.price} ₽</span>
              <span className="plan-price-alt">{p.stars} ⭐</span>
              <span className="plan-price-alt">{p.usdt} USDT</span>
            </div>
          </button>
        ))}
      </div>

      {plan && (
        <div className="payment-methods">
          <p className="method-title">Способ оплаты — <b>{plan.emoji} {plan.name}</b></p>
          <div className="methods-row">
            <button
              className={`method-btn glass-card-sm ${payMethod === "stars" ? "method-active" : ""}`}
              onClick={() => setPayMethod("stars")}
            >
              ⭐ Stars — {plan.stars}
            </button>
            <button
              className={`method-btn glass-card-sm ${payMethod === "usdt" ? "method-active" : ""}`}
              onClick={() => setPayMethod("usdt")}
            >
              💲 USDT — {plan.usdt}
            </button>
          </div>

          {payMethod === "stars" && (
            <button className="pay-btn amber-btn" onClick={handleStarsPay}>
              ⭐ Оплатить {plan.stars} Stars
            </button>
          )}
          {payMethod === "usdt" && (
            <a
              href="https://t.me/BezGranicSupportbot"
              target="_blank"
              rel="noreferrer"
              className="pay-btn usdt-btn"
            >
              📩 Написать для оплаты USDT
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function ReferralTab({
  refCode,
  refLink,
  copied,
  copyRef,
}: {
  refCode: string;
  refLink: string;
  copied: boolean;
  copyRef: () => void;
}) {
  return (
    <div className="tab-content">
      <h2 className="section-title">Реферальная программа</h2>

      <div className="glass-card amber-card ref-card">
        <div className="ref-icon">🎁</div>
        <p className="ref-desc">
          Приглашайте друзей и получайте бонусы за каждого нового пользователя!
        </p>
      </div>

      <div className="glass-card">
        <p className="label-sm">Ваш реферальный код</p>
        <div className="code-box">
          <code className="ref-code-text">{refCode}</code>
        </div>
      </div>

      <div className="glass-card">
        <p className="label-sm">Ваша реферальная ссылка</p>
        <div className="link-row">
          <code className="ref-link-text">{refLink}</code>
        </div>
        <button className={`copy-btn ${copied ? "copied" : ""}`} onClick={copyRef}>
          {copied ? "✅ Скопировано!" : "📋 Скопировать ссылку"}
        </button>
      </div>

      <div className="ref-stats glass-card-sm">
        <div className="stat-item">
          <span className="stat-num">0</span>
          <span className="stat-label">Приглашено</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-num">0 ₽</span>
          <span className="stat-label">Заработано</span>
        </div>
      </div>
    </div>
  );
}

function ProfileTab({
  displayName,
  userIdStr,
  refCode,
}: {
  displayName: string;
  userIdStr: string;
  refCode: string;
}) {
  return (
    <div className="tab-content">
      <h2 className="section-title">Профиль</h2>

      <div className="glass-card amber-card profile-card">
        <div className="avatar-circle">
          {displayName.charAt(displayName.startsWith("@") ? 1 : 0).toUpperCase()}
        </div>
        <p className="profile-name">{displayName}</p>
        <p className="profile-id">ID: <code>{userIdStr}</code></p>
      </div>

      <div className="glass-card profile-info">
        {[
          { label: "Telegram ID",       value: userIdStr,   mono: true  },
          { label: "Подписка",          value: "Не активна", mono: false },
          { label: "Баланс",            value: "0 ₽",        mono: false },
          { label: "Реферальный код",   value: refCode,      mono: true  },
        ].map(row => (
          <div key={row.label} className="info-row">
            <span className="info-label">{row.label}</span>
            {row.mono
              ? <code className="info-value-mono">{row.value}</code>
              : <span className="info-value">{row.value}</span>
            }
          </div>
        ))}
      </div>

      <a
        href="https://t.me/BezGranicVPN_bot"
        target="_blank"
        rel="noreferrer"
        className="pay-btn amber-btn"
      >
        🤖 Открыть бота
      </a>

      <div className="docs-links">
        <a href="https://telegra.ph/Politika-konfidencialnosti-04-01-26" target="_blank" rel="noreferrer" className="doc-link">
          📜 Политика конфиденциальности
        </a>
        <a href="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19" target="_blank" rel="noreferrer" className="doc-link">
          📋 Пользовательское соглашение
        </a>
      </div>
    </div>
  );
}

"""

CSS_CODE = r"""
@import "tailwindcss";

* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --gold:        #facc15;
  --gold-light:  #fde047;
  --gold-dark:   #d97706;
  --gold-dim:    rgba(250, 204, 21, 0.15);
  --gold-glow:   rgba(250, 204, 21, 0.40);
  --bg:          #000000;
  --bg-soft:     #0a0a0a;
  --surface:     rgba(255, 255, 255, 0.04);
  --surface-h:   rgba(255, 255, 255, 0.08);
  --border:      rgba(255, 255, 255, 0.08);
  --border-a:    rgba(250, 204, 21, 0.45);
  --text:        #ffffff;
  --text-muted:  rgba(255, 255, 255, 0.55);
  --radius:      18px;
  --radius-sm:   12px;
  --radius-lg:   28px;
  --ease:        cubic-bezier(0.22, 1, 0.36, 1);
}

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-height: 100dvh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

#root { min-height: 100dvh; }

.app-root {
  position: relative;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: appFadeIn 0.9s var(--ease) both;
}

/* ── ПЛАВНЫЕ ПОЯВЛЕНИЯ ─────────────────────────── */
@keyframes appFadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 20px var(--gold-glow); }
  50%      { box-shadow: 0 0 35px var(--gold-glow), 0 0 60px var(--gold-dim); }
}

@keyframes float {
  0%, 100% { transform: translateY(0) scale(1); }
  50%      { transform: translateY(-10px) scale(1.03); }
}

/* ── ФОНОВЫЕ ОРБЫ ─────────────────────────────── */
.bg-orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(90px);
  pointer-events: none;
  z-index: 0;
  animation: float 8s ease-in-out infinite;
}
.bg-orb-1 {
  width: 360px; height: 360px;
  background: rgba(250, 204, 21, 0.18);
  top: -100px; right: -80px;
}
.bg-orb-2 {
  width: 280px; height: 280px;
  background: rgba(217, 119, 6, 0.14);
  bottom: 80px; left: -100px;
  animation-delay: -3s;
}
.bg-orb-3 {
  width: 220px; height: 220px;
  background: rgba(250, 204, 21, 0.10);
  bottom: 30%; right: 5%;
  animation-delay: -5s;
}

.content-wrap {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 90px;
  position: relative;
  z-index: 1;
  scroll-behavior: smooth;
}

/* ── TAB CONTENT ──────────────────────────────── */
.tab-content {
  padding: 24px 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: fadeInUp 0.65s var(--ease) both;
}

.tab-content > * { animation: fadeInUp 0.65s var(--ease) both; }
.tab-content > *:nth-child(1) { animation-delay: 0.05s; }
.tab-content > *:nth-child(2) { animation-delay: 0.15s; }
.tab-content > *:nth-child(3) { animation-delay: 0.25s; }
.tab-content > *:nth-child(4) { animation-delay: 0.35s; }
.tab-content > *:nth-child(5) { animation-delay: 0.45s; }
.tab-content > *:nth-child(6) { animation-delay: 0.55s; }
.tab-content > *:nth-child(7) { animation-delay: 0.65s; }

/* ── GLASS CARDS ──────────────────────────────── */
.glass-card {
  background: var(--surface);
  border: 1px solid var(--border);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--radius);
  padding: 18px;
  transition: border-color 0.4s var(--ease), transform 0.4s var(--ease), box-shadow 0.4s var(--ease);
}

.glass-card-sm {
  background: var(--surface);
  border: 1px solid var(--border);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-radius: var(--radius-sm);
  padding: 13px 15px;
  transition: all 0.35s var(--ease);
}

.amber-card,
.gold-card {
  border-color: var(--border-a);
  background: linear-gradient(135deg, rgba(250, 204, 21, 0.10), rgba(250, 204, 21, 0.03));
  box-shadow: 0 8px 32px rgba(250, 204, 21, 0.18);
}

/* ── HERO ──────────────────────────────────────── */
.hero-section {
  text-align: center;
  padding: 28px 0 12px;
}

.logo-glow {
  font-size: 64px;
  filter: drop-shadow(0 0 24px var(--gold));
  margin-bottom: 12px;
  animation: float 5s ease-in-out infinite;
}

.hero-title {
  font-size: 26px;
  font-weight: 900;
  letter-spacing: 0.14em;
  background: linear-gradient(135deg, var(--gold-light), #fff 55%, var(--gold));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-sub {
  font-size: 16px;
  color: var(--text);
  margin-top: 8px;
  font-weight: 500;
}

.hero-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 6px;
}

/* ── CARD ROWS ─────────────────────────────────── */
.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.card-label  { font-size: 13px; color: var(--text-muted); }
.card-value  { font-size: 14px; font-weight: 600; color: var(--text); }

.card-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-a), transparent);
  margin: 10px 0;
}

.badge-inactive {
  font-size: 11px;
  padding: 4px 11px;
  border-radius: 20px;
  background: rgba(100, 100, 120, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-muted);
}

.badge-active {
  font-size: 11px;
  padding: 4px 11px;
  border-radius: 20px;
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #4ade80;
}

/* ── FEATURES ──────────────────────────────────── */
.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}
.feature-item:hover {
  border-color: var(--border-a);
  transform: translateY(-2px);
}

.feature-icon { font-size: 20px; }
.feature-text { font-size: 12px; color: var(--text-muted); line-height: 1.35; }

/* ── SUPPORT LINK ──────────────────────────────── */
.support-link {
  display: block;
  text-align: center;
  padding: 14px;
  border-radius: var(--radius-sm);
  background: var(--surface-h);
  border: 1px solid var(--border);
  color: var(--gold-light);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s var(--ease);
}
.support-link:hover {
  background: var(--gold-dim);
  border-color: var(--border-a);
  transform: translateY(-1px);
}

/* ── SECTION TITLE ─────────────────────────────── */
.section-title {
  font-size: 22px;
  font-weight: 800;
  color: var(--text);
  padding-top: 8px;
}

/* ── PLANS ─────────────────────────────────────── */
.plans-list { display: flex; flex-direction: column; gap: 12px; }

.plan-card {
  width: 100%;
  text-align: left;
  cursor: pointer;
  transition: all 0.4s var(--ease);
  background: var(--surface);
  border: 1px solid var(--border);
}
.plan-card:hover {
  border-color: var(--border-a);
  transform: translateY(-2px);
}

.plan-selected {
  border-color: var(--gold) !important;
  background: linear-gradient(135deg, rgba(250, 204, 21, 0.12), rgba(250, 204, 21, 0.04)) !important;
  animation: pulseGlow 2.5s ease-in-out infinite;
}

.plan-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.plan-emoji { font-size: 22px; }
.plan-name  { font-size: 16px; font-weight: 700; color: var(--text); flex: 1; }
.plan-check { color: var(--gold); font-weight: 900; font-size: 18px; }

.plan-prices { display: flex; gap: 14px; flex-wrap: wrap; align-items: center; }

.plan-price-main {
  font-size: 20px;
  font-weight: 800;
  color: var(--gold-light);
}

.plan-price-alt {
  font-size: 13px;
  color: var(--text-muted);
}

/* ── PAYMENT METHODS ───────────────────────────── */
.payment-methods {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: fadeInUp 0.5s var(--ease) both;
}

.method-title {
  font-size: 14px;
  color: var(--text-muted);
}

.methods-row {
  display: flex;
  gap: 10px;
}

.method-btn {
  flex: 1;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: var(--radius-sm);
  padding: 13px 8px;
  transition: all 0.3s var(--ease);
}

.method-active {
  border-color: var(--gold);
  color: var(--gold-light);
  background: var(--gold-dim);
}

.pay-btn {
  display: block;
  width: 100%;
  text-align: center;
  padding: 16px;
  border-radius: var(--radius-lg);
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.35s var(--ease);
}
.pay-btn:hover { transform: translateY(-2px); }
.pay-btn:active { transform: translateY(0); }

.amber-btn,
.gold-btn {
  background: linear-gradient(135deg, var(--gold-light), var(--gold));
  color: #000;
  box-shadow: 0 8px 28px rgba(250, 204, 21, 0.35);
}
.amber-btn:hover,
.gold-btn:hover {
  box-shadow: 0 12px 36px rgba(250, 204, 21, 0.50);
}

.usdt-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
}

/* ── REFERRAL ──────────────────────────────────── */
.ref-card { text-align: center; }
.ref-icon  { font-size: 40px; margin-bottom: 10px; animation: float 4s ease-in-out infinite; }
.ref-desc  { font-size: 13px; color: var(--text-muted); line-height: 1.55; }

.label-sm  { font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }

.code-box {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  text-align: center;
}

.ref-code-text {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 0.10em;
  color: var(--gold-light);
  font-family: 'Courier New', monospace;
}

.link-row {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  word-break: break-all;
}

.ref-link-text {
  font-size: 11px;
  color: var(--text-muted);
  font-family: 'Courier New', monospace;
}

.copy-btn {
  width: 100%;
  padding: 13px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-a);
  background: var(--gold-dim);
  color: var(--gold-light);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s var(--ease);
}
.copy-btn:hover { background: rgba(250, 204, 21, 0.22); }

.copy-btn.copied {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.5);
  color: #34d399;
}

.ref-stats {
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.stat-item { text-align: center; flex: 1; }
.stat-num  { display: block; font-size: 24px; font-weight: 800; color: var(--gold-light); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 3px; display: block; }

.stat-divider {
  width: 1px;
  height: 38px;
  background: var(--border);
}

/* ── PROFILE ───────────────────────────────────── */
.profile-card { text-align: center; }

.avatar-circle {
  width: 78px;
  height: 78px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold-light), var(--gold-dark));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  font-weight: 800;
  color: #000;
  margin: 0 auto 14px;
  box-shadow: 0 0 28px var(--gold-glow);
  animation: pulseGlow 3s ease-in-out infinite;
}

.profile-name { font-size: 19px; font-weight: 700; color: var(--text); }
.profile-id   { font-size: 12px; color: var(--text-muted); margin-top: 5px; }
.profile-id code { color: var(--gold-light); font-family: monospace; }

.profile-info { display: flex; flex-direction: column; gap: 0; }

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  transition: background 0.25s var(--ease);
}

.info-row:last-child { border-bottom: none; }

.info-label     { font-size: 13px; color: var(--text-muted); }
.info-value     { font-size: 13px; font-weight: 600; color: var(--text); }
.info-value-mono { font-size: 12px; font-family: monospace; color: var(--gold-light); }

.docs-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.doc-link {
  display: block;
  text-align: center;
  padding: 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-muted);
  font-size: 13px;
  text-decoration: none;
  transition: all 0.3s var(--ease);
}
.doc-link:hover {
  border-color: var(--border-a);
  color: var(--gold-light);
}

/* ── BOTTOM NAV ────────────────────────────────── */
.bottom-nav {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  z-index: 100;
  display: flex;
  background: rgba(0, 0, 0, 0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-top: 1px solid var(--border);
  padding: 10px 0 env(safe-area-inset-bottom, 0px);
  animation: fadeInUp 0.7s var(--ease) 0.2s both;
}

.nav-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 0;
  transition: all 0.25s var(--ease);
}

.nav-icon  { font-size: 22px; transition: filter 0.3s var(--ease), transform 0.3s var(--ease); }

.nav-label {
  font-size: 10px;
  color: var(--text-muted);
  transition: color 0.25s var(--ease);
  font-weight: 500;
}

.nav-btn.active .nav-label { color: var(--gold-light); }
.nav-btn.active .nav-icon  {
  filter: drop-shadow(0 0 8px var(--gold));
  transform: translateY(-2px) scale(1.1);
}

"""

