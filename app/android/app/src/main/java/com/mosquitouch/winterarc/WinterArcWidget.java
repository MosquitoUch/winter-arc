package com.mosquitouch.winterarc;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.view.View;
import android.widget.RemoteViews;
import org.json.JSONObject;

/** Homescreen-Widget: Tag im Arc, heutige Einheit, Sätze, Quest und Serie. */
public class WinterArcWidget extends AppWidgetProvider {
    static final String PREFS = "wa_widget";
    static final String KEY = "data";

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] ids) {
        for (int id : ids) render(context, manager, id);
    }

    static void updateAll(Context context) {
        AppWidgetManager manager = AppWidgetManager.getInstance(context);
        int[] ids = manager.getAppWidgetIds(new ComponentName(context, WinterArcWidget.class));
        for (int id : ids) render(context, manager, id);
    }

    private static String s(JSONObject o, String k, String def) {
        if (o == null) return def;
        String v = o.optString(k, def);
        return v == null ? def : v;
    }

    static void render(Context context, AppWidgetManager manager, int id) {
        JSONObject o = null;
        try {
            String raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString(KEY, null);
            if (raw != null) o = new JSONObject(raw);
        } catch (Exception ignored) { o = null; }

        RemoteViews v = new RemoteViews(context.getPackageName(), R.layout.widget_wa);
        v.setTextViewText(R.id.wa_day, s(o, "day", "Winter Arc"));
        v.setTextViewText(R.id.wa_rank, s(o, "rank", ""));
        v.setTextViewText(R.id.wa_title, s(o, "title", "Öffne die App"));
        v.setTextViewText(R.id.wa_line, s(o, "line", "Dein Tag wartet."));
        String foot = s(o, "foot", "");
        v.setTextViewText(R.id.wa_foot, foot);
        v.setViewVisibility(R.id.wa_foot, foot.isEmpty() ? View.GONE : View.VISIBLE);
        int pct = o == null ? 0 : Math.max(0, Math.min(100, o.optInt("pct", 0)));
        v.setProgressBar(R.id.wa_bar, 100, pct, false);

        Intent open = new Intent(context, MainActivity.class);
        open.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pi = PendingIntent.getActivity(context, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        v.setOnClickPendingIntent(R.id.wa_root, pi);
        manager.updateAppWidget(id, v);
    }
}
